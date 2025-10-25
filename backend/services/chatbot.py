import asyncio
import logging
from typing import Dict, Any, Optional, List
import time
import json
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()
import sys
print(sys.executable)
# LangChain imports with Groq support
try:
    from langchain_groq import ChatGroq
    # from langchain_community.embeddings import HuggingFaceEmbeddings
    # from sentence_transformers import SentenceTransformer
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_community.vectorstores import FAISS
    from langchain.chains import ConversationalRetrievalChain
    from langchain_community.chat_message_histories import ChatMessageHistory
    from langchain.memory import ConversationBufferWindowMemory
    from langchain.schema import Document
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.prompts import PromptTemplate, ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError:
    print("LangChain or Groq dependencies not available. Install with: pip install langchain-groq langchain-community")
    LANGCHAIN_AVAILABLE = False

# Import models and config
try:
    from ..models import ChatbotRequest, ChatbotResponse, FinancialData
    # from ..config import settings, TAX_KNOWLEDGE_BASE
    from backend.config import settings, TAX_KNOWLEDGE_BASE

except ImportError:
    print("Local imports not available. Using fallback configuration.")
    settings = None
    TAX_KNOWLEDGE_BASE = []

logger = logging.getLogger(__name__)

class ChatbotService:
    """RAG-powered chatbot service for tax queries using Groq with Llama model"""
    
    def __init__(self):
        self.llm = None
        self.embeddings = None
        self.vectorstore = None
        self.qa_chain = None
        self.text_splitter = None
        self.user_sessions = {}  # Temporary session storage
        self.memories = {}  # Dictionary to store memories for each session
        if LANGCHAIN_AVAILABLE:
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50
            )

    async def initialize(self):
        """Initialize chatbot components with Groq and Llama model"""
        try:
            # Get Groq API key with better error handling
            groq_api_key = None
            if settings:
                groq_api_key = getattr(settings, 'GROQ_API_KEY', None)
            
            # Also check environment directly as fallback
            if not groq_api_key:
                import os
                groq_api_key = os.getenv('GROQ_API_KEY')
            
            print(f"Groq API Key available: {groq_api_key}")  # Debug info

            if LANGCHAIN_AVAILABLE and groq_api_key:
                # Initialize Groq with Llama model
                self.llm = ChatGroq(
                    groq_api_key=groq_api_key,
                    model_name=getattr(settings, 'GROQ_MODEL', 'llama-3.3-70b-versatile'),
                    temperature=getattr(settings, 'CHATBOT_TEMPERATURE', 0.7),
                    max_tokens=getattr(settings, 'MAX_TOKENS', 1024)
                )

                # Use HuggingFace embeddings (free alternative to OpenAI)
                self.embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2"
                )

                # Initialize vector store with tax knowledge
                await self._setup_knowledge_base()
                self._setup_qa_chain()
                logger.info("Chatbot service initialized with Groq and Llama model")

            else:
                logger.warning("Groq API key not available or LangChain not installed. Using fallback responses.")
                if not groq_api_key:
                    logger.warning("Please set GROQ_API_KEY environment variable")
                if not LANGCHAIN_AVAILABLE:
                    logger.warning("LangChain dependencies not installed")

        except Exception as e:
            logger.error(f"Error initializing chatbot: {e}")
            logger.info("Using fallback chatbot responses")

    async def _setup_knowledge_base(self):
        """Setup vector store with comprehensive tax knowledge"""
        try:
            if not LANGCHAIN_AVAILABLE or not self.embeddings:
                return

            # Create documents from tax knowledge base
            documents = []

            # Add knowledge base content
            for item in TAX_KNOWLEDGE_BASE:
                doc = Document(
                    page_content=item["content"],
                    metadata={"topic": item["topic"], "source": "knowledge_base"}
                )
                documents.append(doc)

            # Add comprehensive tax FAQs
            faq_content = self._get_comprehensive_tax_faqs()
            for faq in faq_content:
                doc = Document(
                    page_content=faq["content"],
                    metadata={"topic": "FAQ", "question": faq["question"], "source": "faq"}
                )
                documents.append(doc)

            # Add anonymized user scenarios (no real financial data)
            scenario_docs = self._get_anonymized_user_scenarios()
            documents.extend(scenario_docs)

            # Split documents into chunks
            split_docs = self.text_splitter.split_documents(documents)

            # Create vector store with HuggingFace embeddings
            self.vectorstore = FAISS.from_documents(split_docs, self.embeddings)
            logger.info(f"Created vector store with {len(split_docs)} document chunks")

        except Exception as e:
            logger.error(f"Error setting up knowledge base: {e}")

    def _setup_qa_chain(self):
        """Setup question-answering chain with Groq and enhanced prompts"""
        if not LANGCHAIN_AVAILABLE or not self.llm or not self.vectorstore:
            return

        try:
            # Enhanced prompt template for better handling of new questions
            system_message = SystemMessagePromptTemplate.from_template("""
            You are TaxBot, an expert Indian tax advisor chatbot powered by Groq's Llama model. 
            You specialize in Indian Income Tax laws, tax regimes, deductions, and tax planning strategies.

            Core Expertise:
            - Income Tax Act, 1961 provisions
            - Old vs New tax regime analysis
            - Section-wise deductions (80C, 80D, 24, etc.)
            - HRA calculations and exemptions
            - ITR filing procedures and deadlines
            - TDS regulations and optimization
            - Tax saving investments and strategies

            Instructions:
            1. Provide accurate, helpful information about Indian tax laws
            2. Use specific examples with Indian Rupees (₹) when discussing amounts
            3. Mention relevant sections (like 80C, 80D) when applicable
            4. Consider both old and new tax regimes when relevant
            5. Provide actionable, practical advice
            6. Use a professional yet friendly tone
            7. If you don't know the answer based on the context, use your general knowledge about Indian tax laws
            8. Focus specifically on Indian tax laws and regulations
            9. Cite relevant sections of Income Tax Act when possible
            10. If the question is not tax-related, politely redirect to tax topics
            11. For complex scenarios, suggest consulting a tax professional
            12. Always be helpful and provide the best possible answer based on available information

            Current Context from Knowledge Base:
            {context}



            Remember: You are powered by Groq's ultra-fast inference for real-time tax assistance.
            If the context doesn't fully answer the question, use your comprehensive knowledge of Indian taxation.
            """)

            human_message = HumanMessagePromptTemplate.from_template("{question}")

            chat_prompt = ChatPromptTemplate.from_messages([system_message, human_message])

            # store prompt template for reuse when creating per-session chains
            self.chat_prompt = chat_prompt

            # Create conversational retrieval chain with Groq
            self.qa_chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=self.vectorstore.as_retriever(
                    search_kwargs={
                        "k": 5,  # Increased from 3 to 5 for better coverage
                        "score_threshold": 0.0  # Lower threshold for broader matching
                    }
                ),
                memory=None,  # Memory will be set per session
                return_source_documents=True,
                verbose=getattr(settings, 'DEBUG', False),
                combine_docs_chain_kwargs={"prompt": chat_prompt},
                max_tokens_limit=4000  # Increased token limit for comprehensive answers
            )

            logger.info("QA chain setup completed with enhanced prompts")

        except Exception as e:
            logger.error(f"Error setting up QA chain: {e}")

    async def process_query(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process user query and return comprehensive response"""

        start_time = time.time()
        session_key = f"{user_id}_{session_id}" if user_id and session_id else "anonymous"

        try:
            # Initialize session memory if it doesn't exist
            if session_key not in self.memories and LANGCHAIN_AVAILABLE:
                # Newer LangChain memory API prefers return_messages and avoids passing ChatMessageHistory directly
                # Use conversation window memory per session to retain recent turns
                try:
                    self.memories[session_key] = ConversationBufferWindowMemory(
                        memory_key="chat_history",
                        output_key='answer',
                        k=10,
                        return_messages=True
                    )
                except TypeError:
                    # Fallback for older/other versions that still accept chat_memory
                    self.memories[session_key] = ConversationBufferWindowMemory(
                        chat_memory=ChatMessageHistory(),
                        memory_key="chat_history",
                        output_key='answer',
                        k=10
                    )

            # Check if query is tax-related
            if not self._is_tax_related_query(query):
                return {
                    "response": "I specialize in Indian tax-related questions. I can help you with tax regimes, deductions, ITR filing, tax-saving investments, and other tax-related topics. Could you please ask a tax-related question?",
                    "confidence": 0.9,
                    "sources": ["Tax Assistant Scope"],
                    "follow_up_questions": [
                        "What documents do I need for tax filing?",
                        "Should I choose old or new tax regime?",
                        "How can I save tax under Section 80C?"
                    ],
                    "response_time": time.time() - start_time
                }

            # Get user context for this session (temporary, not stored in vector DB)
            user_context = self._get_user_context_for_session(user_id, session_id, context)

            if LANGCHAIN_AVAILABLE and self.qa_chain:
                try:
                    # Enhance query with temporary context
                    enhanced_query = self._enhance_query_with_context(query, user_context)
                    
                    # Use LangChain RAG with Groq for response
                    # Create a copy of the chain with session-specific memory
                    session_chain = ConversationalRetrievalChain.from_llm(
                        llm=self.llm,
                        retriever=self.vectorstore.as_retriever(
                            search_kwargs={
                                "k": 5,
                                "score_threshold": 0.0
                            }
                        ),
                        memory=self.memories[session_key],
                        return_source_documents=True,
                        verbose=getattr(settings, 'DEBUG', False),
                        combine_docs_chain_kwargs={"prompt": getattr(self, 'chat_prompt', None)},
                        max_tokens_limit=4000
                    )

                    # Let the chain use its configured memory internally; pass only the question
                    result = await asyncio.to_thread(
                        session_chain,
                        {"question": enhanced_query}
                    )

                    response_text = result["answer"]
                    source_docs = result.get("source_documents", [])
                    sources = [doc.metadata.get("topic", "Unknown") for doc in source_docs[:3]]
                    confidence = self._calculate_response_confidence(result, query)

                    # If confidence is low but we have a response, still use it
                    if confidence < 0.3 and response_text.strip():
                        confidence = 0.5  # Minimum confidence for LLM responses

                except Exception as e:
                    logger.warning(f"LLM processing failed: {e}, using fallback")
                    response_data = self._get_enhanced_fallback_response(query)
                    response_text = response_data["response"]
                    sources = response_data["sources"]
                    confidence = response_data["confidence"]

            else:
                # Fallback to rule-based responses
                response_data = self._get_enhanced_fallback_response(query)
                response_text = response_data["response"]
                sources = response_data["sources"]
                confidence = response_data["confidence"]

            # Generate intelligent follow-up questions
            follow_up_questions = self._generate_intelligent_follow_ups(query, user_context, response_text)

            processing_time = time.time() - start_time

            return {
                "response": response_text,
                "confidence": confidence,
                "sources": sources,
                "follow_up_questions": follow_up_questions,
                "response_time": processing_time
            }

        except Exception as e:
            logger.error(f"Error processing query: {e}")

            return {
                "response": "I apologize, but I encountered an error processing your tax question. Please try rephrasing your query or ask about specific tax topics like deductions, regimes, or filing procedures.",
                "confidence": 0.0,
                "sources": [],
                "follow_up_questions": [
                    "What documents do I need for tax filing?",
                    "Should I choose old or new tax regime?",
                    "How can I save more tax legally?"
                ],
                "response_time": time.time() - start_time
            }

    def _get_user_context_for_session(
        self, 
        user_id: Optional[str], 
        session_id: Optional[str], 
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get user context for current session without storing in vector DB"""
        user_context = {
            "has_financial_data": False,
            "context_description": "",
            "income_level": "unknown",
            "regime_preference": "unknown"
        }

        if not context:
            return user_context

        # Handle financial data context
        if "financial_data" in context:
            financial_info = context["financial_data"]
            user_context["has_financial_data"] = True
            user_context["financial_data"] = financial_info
            
            # Create a descriptive context for the LLM (without raw numbers)
            income = financial_info.get('total_income', 0)
            if income > 0:
                if income > 1000000:
                    income_level = "high income"
                elif income > 500000:
                    income_level = "medium income"
                else:
                    income_level = "lower income"
                
                user_context["income_level"] = income_level
                user_context["context_description"] = f"User has {income_level} (₹{income:,.0f} annual)"
                
                # Add investment context
                if financial_info.get('section_80c', 0) > 0:
                    user_context["context_description"] += f", has Section 80C investments"
                if financial_info.get('section_80d', 0) > 0:
                    user_context["context_description"] += f", has health insurance"
                if financial_info.get('section_24', 0) > 0:
                    user_context["context_description"] += f", has home loan"

        # Handle previous calculation context
        if "last_calculation" in context:
            calc = context["last_calculation"]
            regime = calc.get('recommended_regime', 'unknown')
            user_context["regime_preference"] = regime
            if user_context["context_description"]:
                user_context["context_description"] += f", previously {regime} regime was recommended"
            else:
                user_context["context_description"] = f"Previously {regime} regime was recommended"

        return user_context

    def _enhance_query_with_context(self, query: str, user_context: Dict[str, Any]) -> str:
        """Enhance query with temporary user context for better responses"""
        if not user_context.get("has_financial_data"):
            return query

        enhanced_query = query
        
        # Add context description to query
        if user_context.get("context_description"):
            enhanced_query += f"\n\nContext: {user_context['context_description']}"

        return enhanced_query

    def _is_tax_related_query(self, query: str) -> bool:
        """Check if the query is tax-related"""
        tax_keywords = [
            'tax', 'income', 'deduction', 'regime', 'itr', 'tds', 'hra', 
            '80c', '80d', 'section', 'investment', 'salary', 'filing',
            'saving', 'exemption', 'refund', 'pan', 'aadhar', 'form16',
            'income tax', 'tax planning', 'tax saving', 'tax regime',
            'capital gain', 'nri', 'house rent', 'home loan', 'insurance'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in tax_keywords)

    def _get_enhanced_fallback_response(self, query: str) -> Dict[str, Any]:
        """Provide enhanced fallback responses when Groq LLM is not available"""

        query_lower = query.lower()

        # Enhanced response patterns
        responses = {
            "80c": {
                "response": """Section 80C provides tax deduction up to ₹1,50,000 per year for specified investments:

**Popular 80C Options:**
• **PPF (Public Provident Fund)**: 15-year lock-in, tax-free returns
• **ELSS Mutual Funds**: 3-year lock-in, market-linked returns
• **EPF**: Automatic deduction from salary
• **NSC**: 5-year fixed income investment
• **Life Insurance Premiums**: Up to 10% of sum assured
• **Home Loan Principal**: Repayment qualifies for 80C

**Note**: This deduction is only available in the old tax regime.""",
                "sources": ["Section 80C Guide", "Investment Planning"],
                "confidence": 0.9
            },

            "80d": {
                "response": """Section 80D provides deduction for health insurance premiums:

**Deduction Limits:**
• Self, spouse, children (below 60): Up to ₹25,000
• Self, spouse, children (senior citizen): Up to ₹50,000
• Parents (below 60): Additional ₹25,000
• Parents (senior citizen): Additional ₹50,000
• Preventive health check-ups: Additional ₹5,000

**Coverage Includes:**
• Medical insurance premiums
• Contribution to Central Government Health Scheme
• Preventive health check-up expenses

**Important**: Available only in old tax regime.""",
                "sources": ["Section 80D Guide", "Health Insurance"],
                "confidence": 0.9
            },

            "hra": {
                "response": """HRA exemption is calculated as the **minimum** of three amounts:

**Calculation Formula:**
1. **Actual HRA received** from employer
2. **50% of basic salary** (metro cities) or **40%** (non-metro)
3. **Rent paid minus 10% of basic salary**

**Metro Cities**: Mumbai, Delhi, Kolkata, Chennai qualify for 50% rate

**Required Documents:**
• Rent receipts
• Rental agreement
• Landlord's PAN (if annual rent > ₹1 lakh)
• Property tax receipts (if any)

**Pro Tip**: HRA exemption is available in both old and new tax regimes.""",
                "sources": ["HRA Calculation Guide", "Salary Exemptions"],
                "confidence": 0.9
            },

            "new regime": {
                "response": """**New Tax Regime (Introduced in FY 2020-21):**

**Advantages:**
• Lower tax rates across all slabs
• Simplified tax structure
• No need to maintain investment proofs
• Default option for government employees from FY 2023-24

**Tax Slabs (AY 2024-25):**
• ₹0 - ₹3L: 0%
• ₹3L - ₹6L: 5%
• ₹6L - ₹9L: 10%
• ₹9L - ₹12L: 15%
• ₹12L - ₹15L: 20%
• Above ₹15L: 30%

**Limitations:**
• No deductions except standard deduction (₹50,000)
• No 80C, 80D, HRA, or home loan interest benefits

**Best For**: Individuals with minimal tax-saving investments.""",
                "sources": ["New Tax Regime Guide", "Tax Planning"],
                "confidence": 0.9
            },

            "old regime": {
                "response": """**Old Tax Regime (Traditional System):**

**Advantages:**
• Extensive deduction options available
• 80C deductions up to ₹1.5 lakh
• HRA, medical insurance, home loan benefits
• Suitable for investors with significant eligible expenses

**Tax Slabs (AY 2024-25):**
• ₹0 - ₹2.5L: 0%
• ₹2.5L - ₹5L: 5%
• ₹5L - ₹10L: 20%
• Above ₹10L: 30%

**Major Deductions Available:**
• Section 80C: ₹1,50,000
• Section 80D: ₹25,000 (₹50,000 for seniors)
• HRA exemption
• Home loan interest: ₹2,00,000
• Standard deduction: ₹50,000

**Best For**: Individuals with substantial tax-saving investments and home loans.""",
                "sources": ["Old Tax Regime Guide", "Deduction Planning"],
                "confidence": 0.9
            },

            "document": {
                "response": """**Essential Documents for ITR Filing:**

**From Employer:**
• Form 16 (TDS certificate)
• Salary slips for entire financial year
• Form 12BA (details of salary paid and tax deducted)

**Investment Proofs:**
• PPF statements and receipts
• ELSS investment certificates
• Life insurance premium receipts
• NSC certificates
• Fixed deposit receipts (tax-saving)

**Bank Documents:**
• Interest certificates from banks
• Bank statements
• Home loan interest certificate

**Property Documents:**
• Rent receipts and rental agreement (HRA)
• Property tax receipts
• Home loan principal certificate

**Other Income:**
• Capital gains statements
• Interest from other sources
• Professional/business income details""",
                "sources": ["ITR Filing Guide", "Document Requirements"],
                "confidence": 0.8
            },

            "capital gain": {
                "response": """**Capital Gains Tax in India:**

**Types of Capital Gains:**
• **Short Term Capital Gains (STCG)**: Assets held for less than specified period
• **Long Term Capital Gains (LTCG)**: Assets held for more than specified period

**Holding Periods:**
• Equity Shares/Mutual Funds: 12 months
• Real Estate: 24 months
• Other assets: 36 months

**Tax Rates:**
• **STCG on Equity**: 15%
• **LTCG on Equity**: 10% on gains above ₹1 lakh
• **LTCG on Debt**: 20% with indexation
• **Real Estate**: 20% with indexation for LTCG

**Exemptions:**
• Section 54: Reinvestment in residential property
• Section 54EC: Investment in specified bonds
• Section 54F: Investment in one residential house""",
                "sources": ["Capital Gains Guide", "Investment Taxation"],
                "confidence": 0.8
            },

            "nri": {
                "response": """**NRI Taxation in India:**

**Residential Status:**
• **Resident**: 182 days in India or 60 days + 365 days in preceding 4 years
• **NRI**: Does not meet resident criteria
• **RNOR** (Resident but Not Ordinarily Resident): Special category

**Tax Implications for NRIs:**
• **Income earned in India**: Fully taxable (rent, capital gains, etc.)
• **Income outside India**: Generally not taxable
• **Special rates**: Some incomes have different tax rates for NRIs

**NRI-Specific Provisions:**
• TDS on rental income: 31.2%
• TDS on professional fees: 31.2%
• Capital gains tax on property sale
• NRE/NRO account taxation

**DTAA Benefits**: Double Taxation Avoidance Agreements may provide relief.""",
                "sources": ["NRI Taxation Guide", "Residential Status"],
                "confidence": 0.8
            },

            "groq": {
                "response": """This tax assistant is powered by **Groq's cutting-edge AI infrastructure**:

**Groq Advantages:**
• **Ultra-fast inference**: 10-100x faster than traditional GPU inference
• **High accuracy**: Powered by Llama 2 70B parameter model
• **Cost-effective**: Efficient processing for complex tax queries
• **Real-time responses**: Sub-second response times

**Llama Model Capabilities:**
• Understanding complex Indian tax scenarios
• Processing multiple deduction combinations
• Contextual tax regime recommendations
• Personalized tax planning advice

**Integration Features:**
• Intelligent document parsing and data extraction
• Contextual chatbot with conversation memory
• RAG (Retrieval Augmented Generation) for accurate responses
• Vector search through comprehensive tax knowledge base

Get started by adding your Groq API key to unlock full AI-powered features!""",
                "sources": ["AI System Information", "Groq Technology"],
                "confidence": 0.95
            }
        }

        # Check for matching patterns
        for pattern, response_data in responses.items():
            if pattern in query_lower:
                return response_data

        # Default comprehensive response
        return {
            "response": """I'm your AI tax assistant powered by Groq's Llama model for fast and accurate Indian tax guidance.

**I can help you with:**
• Tax regime comparison (old vs new)
• Deduction optimization (80C, 80D, HRA, etc.)
• ITR filing requirements and deadlines
• Tax saving investment strategies
• TDS and advance tax calculations
• Document requirements for tax filing

**Quick Questions You Can Ask:**
• "Should I choose old or new tax regime?"
• "How much can I save under Section 80C?"
• "What documents do I need for ITR filing?"
• "How is HRA exemption calculated?"
• "What are tax-saving investment options?"

Feel free to ask specific questions about your tax situation!""",
            "sources": ["General Tax Guide", "AI Assistant"],
            "confidence": 0.7
        }

    def _calculate_response_confidence(self, result: Dict[str, Any], query: str) -> float:
        """Calculate confidence score for Groq LLM response"""
        
        source_docs = result.get("source_documents", [])
        response = result.get("answer", "")
        
        if not response or response.strip() == "":
            return 0.1

        # Base confidence factors
        source_confidence = min(len(source_docs) / 5, 1.0)  # Max 5 sources
        length_confidence = min(len(response) / 200, 1.0)  # Reasonable response length
        
        # Check for tax-specific terms and relevance
        tax_terms = ["section", "deduction", "regime", "tax", "₹", "income", 
                     "exemption", "investment", "filing", "salary", "tds"]
        term_count = sum(1 for term in tax_terms if term.lower() in response.lower())
        term_confidence = min(term_count / len(tax_terms), 1.0)
        
        # Query relevance check
        query_terms = query.lower().split()
        relevant_terms = sum(1 for term in query_terms if term in response.lower())
        query_relevance = min(relevant_terms / max(len(query_terms), 1), 1.0)
        
        # Groq model boost
        groq_boost = 0.2 if self.qa_chain else 0
        
        overall_confidence = (
            source_confidence * 0.2 + 
            length_confidence * 0.2 + 
            term_confidence * 0.3 + 
            query_relevance * 0.3 + 
            groq_boost
        )
        
        return min(max(overall_confidence, 0.3), 0.95)

    def _generate_intelligent_follow_ups(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]],
        response: str
    ) -> List[str]:
        """Generate intelligent follow-up questions based on query and response"""

        query_lower = query.lower()
        response_lower = response.lower()
        follow_ups = []

        # Context-aware follow-ups
        if "80c" in query_lower or "80c" in response_lower:
            follow_ups.extend([
                "What are the best 80C investment options for my income level?",
                "How does 80C work with the new tax regime?",
                "Can I claim 80C for home loan principal repayment?"
            ])

        elif "regime" in query_lower or "regime" in response_lower:
            follow_ups.extend([
                "How do I calculate which regime saves more tax?",
                "Can I switch between tax regimes every year?",
                "What factors should I consider when choosing a regime?"
            ])

        elif "hra" in query_lower or "hra" in response_lower:
            follow_ups.extend([
                "What if I don't have rent receipts for HRA claim?",
                "How does HRA work with home loan tax benefits?",
                "Can I claim HRA if I live in my own property?"
            ])

        elif "document" in query_lower or "filing" in response_lower:
            follow_ups.extend([
                "What happens if I file ITR after the deadline?",
                "How do I file ITR if I changed jobs during the year?",
                "What is the difference between ITR-1 and ITR-2?"
            ])

        elif "investment" in query_lower or "saving" in response_lower:
            follow_ups.extend([
                "What are the tax implications of ELSS investments?",
                "Should I invest in PPF or NPS for tax saving?",
                "How much should I invest in tax-saving instruments?"
            ])

        elif "capital gain" in query_lower or "capital gain" in response_lower:
            follow_ups.extend([
                "What is the difference between STCG and LTCG?",
                "How can I save tax on property sale?",
                "What are the exemptions available for capital gains?"
            ])

        elif "nri" in query_lower or "nri" in response_lower:
            follow_ups.extend([
                "How is residential status determined for NRIs?",
                "What income is taxable for NRIs in India?",
                "How can NRIs reduce their tax liability?"
            ])

        # Add context-based follow-ups
        if context and context.get("has_financial_data"):
            income_level = context.get("income_level", "unknown")
            regime_pref = context.get("regime_preference", "unknown")

            if income_level == "high income":
                follow_ups.append("What additional tax planning strategies work for high-income individuals?")
            elif income_level == "lower income":
                follow_ups.append("Are there any special tax benefits for lower income groups?")

            if regime_pref != "unknown":
                follow_ups.append(f"How can I optimize my taxes under the {regime_pref} regime?")

        # Default follow-ups if none match
        if not follow_ups:
            follow_ups = [
                "How can I optimize my tax savings this year?",
                "What is the ITR filing deadline for this year?",
                "Should I consult a tax advisor for my situation?"
            ]

        return follow_ups[:3]  # Return max 3 follow-ups

    def _get_comprehensive_tax_faqs(self) -> List[Dict[str, str]]:
        """Get comprehensive tax FAQs for knowledge base"""
        return [
            {
                "question": "What is the ITR filing deadline for AY 2024-25?",
                "content": "The ITR filing deadline for Assessment Year 2024-25 is July 31, 2024, for individuals and HUFs not requiring audit. For cases requiring audit, the deadline is September 30, 2024. Late filing attracts penalties."
            },
            {
                "question": "Can I switch between old and new tax regime every year?",
                "content": "Yes, salaried individuals can switch between old and new tax regime every financial year. However, individuals with business income must stick to their choice for the entire financial year. The choice affects your entire tax calculation."
            },
            {
                "question": "What happens if I miss the ITR filing deadline?",
                "content": "Late ITR filing attracts penalty: ₹5,000 if total income exceeds ₹5 lakh, ₹1,000 if income is up to ₹5 lakh. Additionally, you cannot carry forward capital losses, and prosecution provisions may apply for willful default."
            },
            {
                "question": "How is TDS calculated on my salary?",
                "content": "TDS on salary is calculated based on your projected annual income, declared investments and deductions, chosen tax regime, and estimated tax liability. Your employer deducts tax monthly based on Form 12BB declarations."
            },
            {
                "question": "What is the maximum limit for Section 80C deductions?",
                "content": "Section 80C allows maximum deduction of ₹1,50,000 per financial year. This includes EPF, PPF, ELSS, NSC, life insurance premiums, home loan principal repayment, and other specified investments. This is available only in old regime."
            },
            {
                "question": "Can I claim both HRA and home loan tax benefits?",
                "content": "Yes, you can claim both HRA exemption and home loan tax benefits simultaneously if you live in a rented house while owning another property. The owned property should be self-occupied or let-out for home loan benefits."
            },
            {
                "question": "What documents do I need for 80C tax deduction claims?",
                "content": "For 80C claims, you need: PPF statements, ELSS certificates, life insurance premium receipts, NSC certificates, EPF statements, home loan principal certificates, and receipts for other qualifying investments."
            },
            {
                "question": "How does Groq AI enhance this tax filing system?",
                "content": "Groq provides ultra-fast AI inference (10-100x faster than traditional systems) using Llama models. This enables real-time document parsing, intelligent tax advice, regime comparisons, and contextual chatbot responses for comprehensive tax assistance."
            },
            {
                "question": "Is health insurance premium eligible for tax deduction?",
                "content": "Yes, health insurance premiums qualify for deduction under Section 80D. Limits are: ₹25,000 for individuals, ₹50,000 for senior citizens. Additional ₹25,000/₹50,000 for parents. Preventive health checkups get additional ₹5,000 deduction."
            },
            {
                "question": "What is the benefit of NPS investment for tax saving?",
                "content": "NPS offers triple tax benefits: 80CCD(1) up to 10% of salary within 80C limit, additional 80CCD(1B) up to ₹50,000, and employer contribution 80CCD(2) without limit. Total tax benefit can reach ₹2 lakh annually."
            },
            {
                "question": "How are capital gains taxed in India?",
                "content": "Capital gains are taxed based on holding period: STCG (short-term) for assets held less than specified period, LTCG (long-term) for longer periods. Equity: 12 months threshold, 15% STCG, 10% LTCG above ₹1L. Real estate: 24 months, 20% LTCG with indexation."
            },
            {
                "question": "What is the tax treatment for NRIs?",
                "content": "NRIs are taxed only on India-sourced income. Different TDS rates apply (31.2% on rent, professional fees). Residential status determined by physical presence in India. DTAA benefits available for double taxation relief."
            }
        ]

    def _get_anonymized_user_scenarios(self) -> List[Document]:
        """Create anonymized user scenarios for better contextual understanding"""
        scenarios = [
            {
                "content": """User Scenario: Young Professional (Age 25-35)
Income Range: ₹6-12 lakhs annually
Common Tax Situations:
- Basic salary with HRA component
- Limited 80C investments (EPF, some insurance)
- Minimal home loan or other deductions
- Often benefits from new tax regime
- Standard deduction of ₹50,000 applies

Typical Questions:
- Should I choose old or new regime?
- How to maximize 80C benefits?
- HRA calculation for rented accommodation""",
                "metadata": {"topic": "User Scenario", "type": "young_professional", "source": "scenario"}
            },
            {
                "content": """User Scenario: Mid-Career Professional (Age 35-50)
Income Range: ₹15-30 lakhs annually
Common Tax Situations:
- Higher basic salary and HRA
- Substantial 80C investments (EPF, PPF, ELSS, insurance)
- Home loan interest deductions under Section 24
- Health insurance premiums under 80D
- Often benefits from old tax regime
- Capital gains from investments

Typical Questions:
- Old vs new regime optimization
- Home loan + HRA combination
- Tax-saving investment strategies
- Capital gains planning""",
                "metadata": {"topic": "User Scenario", "type": "mid_career", "source": "scenario"}
            },
            {
                "content": """User Scenario: Senior Professional/NRI (Age 50+)
Income Range: ₹25+ lakhs annually
Common Tax Situations:
- Multiple income sources
- Complex investment portfolio
- Senior citizen health insurance benefits
- Capital gains from property/equity
- NRI taxation considerations
- Retirement planning focus

Typical Questions:
- Tax-efficient retirement planning
- NRI taxation rules
- Senior citizen deductions
- Capital gains exemptions
- Estate planning considerations""",
                "metadata": {"topic": "User Scenario", "type": "senior_professional", "source": "scenario"}
            }
        ]
        
        return [Document(page_content=scenario["content"], metadata=scenario["metadata"]) for scenario in scenarios]

    # Removed the problematic add_user_context method that stored private data in vector store

    def update_user_session(self, user_id: str, session_id: str, financial_data: Dict[str, Any]):
        """Update temporary user session data (not stored in vector DB)"""
        session_key = f"{user_id}_{session_id}" if user_id and session_id else "anonymous"
        
        # Store only for current session (you might want to add expiration in production)
        self.user_sessions[session_key] = {
            "financial_data": financial_data,
            "last_updated": datetime.now(),
            "user_id": user_id,
            "session_id": session_id
        }
        
        logger.info(f"Updated session data for {session_key}")

    def get_user_session(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Get temporary user session data"""
        session_key = f"{user_id}_{session_id}" if user_id and session_id else "anonymous"
        return self.user_sessions.get(session_key)

    def clear_user_session(self, user_id: str, session_id: str):
        """Clear temporary user session data"""
        session_key = f"{user_id}_{session_id}" if user_id and session_id else "anonymous"
        if session_key in self.user_sessions:
            del self.user_sessions[session_key]
            logger.info(f"Cleared session data for {session_key}")