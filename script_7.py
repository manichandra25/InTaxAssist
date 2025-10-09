# Create chatbot service
chatbot_service_content = '''import asyncio
import logging
from typing import Dict, Any, Optional, List
import time
import json
from datetime import datetime

# LangChain imports with fallback handling
try:
    from langchain.llms import OpenAI
    from langchain.embeddings import OpenAIEmbeddings
    from langchain.vectorstores import FAISS
    from langchain.chains import ConversationalRetrievalChain
    from langchain.memory import ConversationBufferWindowMemory
    from langchain.schema import Document
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.prompts import PromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

# Import models and config
from models import ChatbotRequest, ChatbotResponse, FinancialData
from config import settings, TAX_KNOWLEDGE_BASE

logger = logging.getLogger(__name__)

class ChatbotService:
    """RAG-powered chatbot service for tax queries"""
    
    def __init__(self):
        self.llm = None
        self.embeddings = None
        self.vectorstore = None
        self.qa_chain = None
        self.memory = None
        self.text_splitter = None
        
        if LANGCHAIN_AVAILABLE:
            self.memory = ConversationBufferWindowMemory(
                memory_key="chat_history",
                return_messages=True,
                k=settings.MAX_CHAT_HISTORY
            )
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50
            )
        
    async def initialize(self):
        """Initialize chatbot components"""
        try:
            if LANGCHAIN_AVAILABLE and settings.OPENAI_API_KEY:
                self.llm = OpenAI(
                    openai_api_key=settings.OPENAI_API_KEY,
                    temperature=settings.CHATBOT_TEMPERATURE
                )
                self.embeddings = OpenAIEmbeddings(
                    openai_api_key=settings.OPENAI_API_KEY
                )
                
                # Initialize vector store with tax knowledge
                await self._setup_knowledge_base()
                self._setup_qa_chain()
                logger.info("Chatbot service initialized with LangChain")
                
            else:
                logger.warning("LangChain not available or API key missing. Using fallback responses.")
                
        except Exception as e:
            logger.error(f"Error initializing chatbot: {e}")
            logger.info("Using fallback chatbot responses")

    async def _setup_knowledge_base(self):
        """Setup vector store with tax knowledge"""
        try:
            if not LANGCHAIN_AVAILABLE or not self.embeddings:
                return
                
            # Create documents from tax knowledge base
            documents = []
            
            for item in TAX_KNOWLEDGE_BASE:
                doc = Document(
                    page_content=item["content"],
                    metadata={"topic": item["topic"]}
                )
                documents.append(doc)
            
            # Add common tax FAQs
            faq_content = self._get_tax_faqs()
            for faq in faq_content:
                doc = Document(
                    page_content=faq["content"],
                    metadata={"topic": "FAQ", "question": faq["question"]}
                )
                documents.append(doc)
            
            # Split documents
            split_docs = self.text_splitter.split_documents(documents)
            
            # Create vector store
            self.vectorstore = FAISS.from_documents(split_docs, self.embeddings)
            logger.info(f"Created vector store with {len(split_docs)} document chunks")
            
        except Exception as e:
            logger.error(f"Error setting up knowledge base: {e}")

    def _setup_qa_chain(self):
        """Setup question-answering chain"""
        if not LANGCHAIN_AVAILABLE or not self.llm or not self.vectorstore:
            return
            
        try:
            # Create conversational retrieval chain
            self.qa_chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=self.vectorstore.as_retriever(search_kwargs={"k": 3}),
                memory=self.memory,
                return_source_documents=True,
                verbose=False
            )
        except Exception as e:
            logger.error(f"Error setting up QA chain: {e}")

    async def process_query(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> ChatbotResponse:
        """Process user query and return response"""
        
        start_time = time.time()
        
        try:
            # Enhance query with context if provided
            enhanced_query = self._enhance_query_with_context(query, context)
            
            if LANGCHAIN_AVAILABLE and self.qa_chain:
                # Use LangChain RAG for response
                result = await asyncio.to_thread(
                    self.qa_chain,
                    {"question": enhanced_query}
                )
                
                response_text = result["answer"]
                source_docs = result.get("source_documents", [])
                sources = [doc.metadata.get("topic", "Unknown") for doc in source_docs]
                confidence = self._calculate_response_confidence(result)
                
            else:
                # Fallback to rule-based responses
                response_data = self._get_fallback_response(query)
                response_text = response_data["response"]
                sources = response_data["sources"]
                confidence = response_data["confidence"]
            
            # Generate follow-up questions
            follow_up_questions = self._generate_follow_up_questions(query, context)
            
            processing_time = time.time() - start_time
            
            return ChatbotResponse(
                response=response_text,
                confidence=confidence,
                sources=sources,
                follow_up_questions=follow_up_questions,
                response_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            
            return ChatbotResponse(
                response="I apologize, but I encountered an error processing your question. Please try rephrasing your query or contact support if the issue persists.",
                confidence=0.0,
                sources=[],
                follow_up_questions=[],
                response_time=time.time() - start_time
            )

    def _enhance_query_with_context(self, query: str, context: Optional[Dict[str, Any]]) -> str:
        """Enhance query with user context"""
        if not context:
            return query
        
        enhanced_query = query
        
        # Add financial context if available
        if "financial_data" in context:
            financial_info = context["financial_data"]
            enhanced_query += f"\\n\\nUser's financial context: Income around ₹{financial_info.get('total_income', 0):,.0f}"
        
        # Add previous calculation context
        if "last_calculation" in context:
            calc = context["last_calculation"]
            enhanced_query += f"\\n\\nPrevious calculation: {calc.get('regime', 'Unknown')} regime with ₹{calc.get('tax', 0):,.0f} tax"
        
        return enhanced_query

    def _get_fallback_response(self, query: str) -> Dict[str, Any]:
        """Provide fallback responses when LLM is not available"""
        
        query_lower = query.lower()
        
        # Define response patterns
        responses = {
            "80c": {
                "response": "Section 80C allows deduction up to ₹1,50,000 for investments in PPF, ELSS, NSC, life insurance premiums, and more. This is available only in the old tax regime.",
                "sources": ["Section 80C Guide"],
                "confidence": 0.8
            },
            "80d": {
                "response": "Section 80D provides deduction for health insurance premiums up to ₹25,000 for individuals (₹50,000 for senior citizens). This applies to premiums paid for yourself, spouse, and dependent children.",
                "sources": ["Section 80D Guide"],
                "confidence": 0.8
            },
            "hra": {
                "response": "HRA exemption is calculated as the minimum of: (1) Actual HRA received, (2) 50% of salary for metro cities or 40% for non-metro, (3) Rent paid minus 10% of salary.",
                "sources": ["HRA Calculation Guide"],
                "confidence": 0.8
            },
            "new regime": {
                "response": "The new tax regime offers lower tax rates but allows fewer deductions. You can only claim standard deduction and employer's contribution to NPS. Most other deductions like 80C, 80D are not available.",
                "sources": ["Tax Regime Comparison"],
                "confidence": 0.8
            },
            "old regime": {
                "response": "The old tax regime has higher tax rates but allows various deductions under sections 80C, 80D, 24, etc. You can claim up to ₹1.5 lakh under 80C plus other deductions.",
                "sources": ["Tax Regime Comparison"],
                "confidence": 0.8
            },
            "document": {
                "response": "For tax filing, you typically need: Form 16, Bank statements, Investment proofs (80C, 80D), Rent receipts for HRA, Home loan statements for Section 24, and any other income proof documents.",
                "sources": ["Document Requirements"],
                "confidence": 0.8
            }
        }
        
        # Check for matching patterns
        for pattern, response_data in responses.items():
            if pattern in query_lower:
                return response_data
        
        # Default response
        return {
            "response": "I can help you with Indian tax filing questions including tax regimes, deductions, HRA calculations, and tax planning. Please ask me specific questions about these topics.",
            "sources": ["General Tax Guide"],
            "confidence": 0.5
        }

    def _calculate_response_confidence(self, result: Dict[str, Any]) -> float:
        """Calculate confidence score for LLM response"""
        
        # Simple confidence calculation based on:
        # 1. Number of source documents
        # 2. Length of response
        # 3. Presence of specific tax terms
        
        source_docs = result.get("source_documents", [])
        response = result.get("answer", "")
        
        source_confidence = min(len(source_docs) / 3, 1.0)  # Max 3 sources
        length_confidence = min(len(response) / 200, 1.0)  # Reasonable length
        
        # Check for tax-specific terms
        tax_terms = ["section", "deduction", "regime", "tax", "₹", "income"]
        term_count = sum(1 for term in tax_terms if term.lower() in response.lower())
        term_confidence = min(term_count / len(tax_terms), 1.0)
        
        overall_confidence = (source_confidence * 0.4) + (length_confidence * 0.3) + (term_confidence * 0.3)
        
        return min(max(overall_confidence, 0.3), 0.95)

    def _generate_follow_up_questions(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Generate relevant follow-up questions"""
        
        query_lower = query.lower()
        follow_ups = []
        
        if "80c" in query_lower:
            follow_ups.extend([
                "What are the best 80C investment options?",
                "Can I claim 80C deduction in the new tax regime?"
            ])
        
        if "regime" in query_lower:
            follow_ups.extend([
                "How do I choose between old and new tax regime?",
                "Can I switch between tax regimes every year?"
            ])
        
        if "deduction" in query_lower:
            follow_ups.extend([
                "What other deductions can I claim?",
                "What is the maximum deduction limit for Section 80D?"
            ])
        
        if "hra" in query_lower:
            follow_ups.extend([
                "What documents are needed for HRA exemption?",
                "Can I claim HRA without rent receipts?"
            ])
        
        if "document" in query_lower:
            follow_ups.extend([
                "How do I upload documents for parsing?",
                "What file formats are supported?"
            ])
        
        # General follow-ups if none match
        if not follow_ups:
            follow_ups = [
                "How can I save more tax legally?",
                "What is the deadline for filing ITR?",
                "Should I choose old or new tax regime?"
            ]
        
        return follow_ups[:3]  # Return max 3 follow-ups

    def _get_tax_faqs(self) -> List[Dict[str, str]]:
        """Get common tax FAQs"""
        return [
            {
                "question": "What is the deadline for filing ITR?",
                "content": "The deadline for filing Income Tax Return (ITR) is July 31st for individuals and HUFs not required to get accounts audited. For businesses requiring audit, it's September 30th."
            },
            {
                "question": "Can I switch between tax regimes?",
                "content": "Salaried individuals can switch between old and new tax regime every year. However, individuals with business income need to stick to their choice for that assessment year."
            },
            {
                "question": "What happens if I file ITR late?",
                "content": "Late filing attracts penalty of ₹5,000 (₹1,000 if income is below ₹5 lakh). You also cannot carry forward certain losses and may face prosecution for willful default."
            },
            {
                "question": "How is TDS calculated on salary?",
                "content": "TDS on salary is calculated based on your projected annual income, deductions claimed, and the tax regime chosen. Employer deducts tax monthly based on estimated annual liability."
            },
            {
                "question": "What are the mandatory documents for ITR filing?",
                "content": "Essential documents include Form 16, bank statements, investment proofs, rent receipts (for HRA), home loan statements, and details of other income sources."
            }
        ]

    async def add_user_context(self, user_id: str, financial_data: FinancialData):
        """Add user-specific financial context for personalized responses"""
        try:
            if not LANGCHAIN_AVAILABLE or not self.vectorstore:
                return
                
            # Create user-specific document
            context_content = f"""
            User Financial Profile:
            - Total Income: ₹{financial_data.total_income:,.0f}
            - Basic Salary: ₹{financial_data.basic_salary:,.0f}
            - HRA: ₹{financial_data.hra:,.0f}
            - Section 80C Investments: ₹{financial_data.section_80c:,.0f}
            - Section 80D Premiums: ₹{financial_data.section_80d:,.0f}
            - Home Loan Interest: ₹{financial_data.section_24:,.0f}
            - TDS Deducted: ₹{financial_data.tds_deducted:,.0f}
            """
            
            user_doc = Document(
                page_content=context_content,
                metadata={"user_id": user_id, "type": "financial_profile"}
            )
            
            # Add to vector store
            self.vectorstore.add_documents([user_doc])
            logger.info(f"Added financial context for user {user_id}")
        
        except Exception as e:
            logger.error(f"Error adding user context: {e}")
'''

# Write chatbot service
with open("tax-filing-system/backend/services/chatbot.py", "w", encoding="utf-8") as f:
    f.write(chatbot_service_content)

print("Created services/chatbot.py - Chatbot service")