import asyncio
import logging
from typing import Dict, Any, Optional, List
import time
import json
from datetime import datetime

# LangChain imports with Groq support
try:
    from langchain_groq import ChatGroq
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import FAISS
    from langchain.chains import ConversationalRetrievalChain
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
    from models import ChatbotRequest, ChatbotResponse, FinancialData
    from config import settings, TAX_KNOWLEDGE_BASE
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
        self.memory = None
        self.text_splitter = None

        if LANGCHAIN_AVAILABLE:
            self.memory = ConversationBufferWindowMemory(
                memory_key="chat_history",
                return_messages=True,
                k=10  # Keep last 10 exchanges
            )
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50
            )

    async def initialize(self):
        """Initialize chatbot components with Groq and Llama model"""
        try:
            groq_api_key = getattr(settings, 'GROQ_API_KEY', None) if settings else None

            if LANGCHAIN_AVAILABLE and groq_api_key:
                # Initialize Groq with Llama model
                self.llm = ChatGroq(
                    groq_api_key=groq_api_key,
                    model_name=getattr(settings, 'GROQ_MODEL', 'llama2-70b-4096'),
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
            # Create a specialized prompt template for Indian tax queries
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
            7. If unsure about something, acknowledge limitations
            8. Focus specifically on Indian tax laws and regulations
            9. Cite relevant sections of Income Tax Act when possible
            10. Provide follow-up questions to help users explore topics deeper

            Current Context from Knowledge Base:
            {context}

            Remember: You are powered by Groq's ultra-fast inference for real-time tax assistance.
            """)

            human_message = HumanMessagePromptTemplate.from_template("{question}")

            chat_prompt = ChatPromptTemplate.from_messages([system_message, human_message])

            # Create conversational retrieval chain with Groq
            self.qa_chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=self.vectorstore.as_retriever(search_kwargs={"k": 3}),
                memory=self.memory,
                return_source_documents=True,
                verbose=False,
                combine_docs_chain_kwargs={"prompt": chat_prompt}
            )

            logger.info("QA chain setup completed with enhanced prompts")

        except Exception as e:
            logger.error(f"Error setting up QA chain: {e}")

    async def process_query(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process user query and return comprehensive response"""

        start_time = time.time()

        try:
            # Enhance query with context if provided
            enhanced_query = self._enhance_query_with_context(query, context)

            if LANGCHAIN_AVAILABLE and self.qa_chain:
                # Use LangChain RAG with Groq for response
                result = await asyncio.to_thread(
                    self.qa_chain,
                    {"question": enhanced_query}
                )

                response_text = result["answer"]
                source_docs = result.get("source_documents", [])
                sources = [doc.metadata.get("topic", "Unknown") for doc in source_docs[:3]]
                confidence = self._calculate_response_confidence(result)

            else:
                # Fallback to rule-based responses
                response_data = self._get_enhanced_fallback_response(query)
                response_text = response_data["response"]
                sources = response_data["sources"]
                confidence = response_data["confidence"]

            # Generate intelligent follow-up questions
            follow_up_questions = self._generate_intelligent_follow_ups(query, context, response_text)

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
                "response": "I apologize, but I encountered an error processing your question. This might be due to a temporary issue with the AI service. Please try rephrasing your query or ask a simpler question.",
                "confidence": 0.0,
                "sources": [],
                "follow_up_questions": [
                    "What documents do I need for tax filing?",
                    "Should I choose old or new tax regime?",
                    "How can I save more tax legally?"
                ],
                "response_time": time.time() - start_time
            }

    def _enhance_query_with_context(self, query: str, context: Optional[Dict[str, Any]]) -> str:
        """Enhance query with user context for better responses"""
        if not context:
            return query

        enhanced_query = query

        # Add financial context if available
        if "financial_data" in context:
            financial_info = context["financial_data"]
            enhanced_query += f"\n\nUser's financial context: Total income around ₹{financial_info.get('total_income', 0):,.0f}"

            # Add deduction context
            if financial_info.get('section_80c', 0) > 0:
                enhanced_query += f", 80C investments: ₹{financial_info.get('section_80c', 0):,.0f}"

        # Add previous calculation context
        if "last_calculation" in context:
            calc = context["last_calculation"]
            regime = calc.get('recommended_regime', 'Unknown')
            tax_amount = calc.get('savings_amount', 0)
            enhanced_query += f"\n\nPrevious tax calculation: {regime} regime recommended with ₹{tax_amount:,.0f} potential savings"

        return enhanced_query

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

    def _calculate_response_confidence(self, result: Dict[str, Any]) -> float:
        """Calculate confidence score for Groq LLM response"""

        source_docs = result.get("source_documents", [])
        response = result.get("answer", "")

        # Confidence factors
        source_confidence = min(len(source_docs) / 3, 1.0)  # Max 3 sources
        length_confidence = min(len(response) / 300, 1.0)  # Reasonable response length

        # Check for tax-specific terms and accuracy indicators
        tax_terms = ["section", "deduction", "regime", "tax", "₹", "income", "exemption", "investment"]
        term_count = sum(1 for term in tax_terms if term.lower() in response.lower())
        term_confidence = min(term_count / len(tax_terms), 1.0)

        # Groq model boost (higher confidence with AI)
        groq_boost = 0.1 if self.qa_chain else 0

        overall_confidence = (source_confidence * 0.3) + (length_confidence * 0.2) + (term_confidence * 0.4) + groq_boost

        return min(max(overall_confidence, 0.2), 0.95)

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

        # Add context-based follow-ups
        if context and "financial_data" in context:
            financial_data = context["financial_data"]
            income = financial_data.get("total_income", 0)

            if income > 1000000:  # High income
                follow_ups.append("What additional tax planning strategies work for high-income individuals?")
            elif income < 500000:  # Lower income
                follow_ups.append("Are there any special tax benefits for lower income groups?")

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
            }
        ]

    async def add_user_context(self, user_id: str, financial_data: Dict[str, Any]):
        """Add user-specific financial context for personalized responses"""
        try:
            if not LANGCHAIN_AVAILABLE or not self.vectorstore:
                return

            # Create user-specific document with financial profile
            context_content = f"""
            User Financial Profile (ID: {user_id}):
            - Total Annual Income: ₹{financial_data.get('total_income', 0):,.0f}
            - Basic Salary: ₹{financial_data.get('basic_salary', 0):,.0f}
            - HRA Component: ₹{financial_data.get('hra', 0):,.0f}
            - Section 80C Investments: ₹{financial_data.get('section_80c', 0):,.0f}
            - Section 80D Premiums: ₹{financial_data.get('section_80d', 0):,.0f}
            - Home Loan Interest (24): ₹{financial_data.get('section_24', 0):,.0f}
            - TDS Deducted: ₹{financial_data.get('tds_deducted', 0):,.0f}

            Profile Analysis:
            - Income Category: {"High" if financial_data.get('total_income', 0) > 1000000 else "Medium" if financial_data.get('total_income', 0) > 500000 else "Lower"}
            - 80C Utilization: {(financial_data.get('section_80c', 0) / 150000 * 100):.1f}% of limit utilized
            - Tax Planning Status: {"Advanced" if financial_data.get('section_80c', 0) > 100000 else "Basic"}
            """

            user_doc = Document(
                page_content=context_content,
                metadata={
                    "user_id": user_id, 
                    "type": "financial_profile",
                    "income_level": financial_data.get('total_income', 0),
                    "timestamp": datetime.now().isoformat()
                }
            )

            # Add to vector store for personalized responses
            self.vectorstore.add_documents([user_doc])
            logger.info(f"Added personalized financial context for user {user_id}")

        except Exception as e:
            logger.error(f"Error adding user context: {e}")
