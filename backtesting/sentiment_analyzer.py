#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Financial Sentiment Analyzer using ChatGLM2-6B Model
Provides sentiment scoring for financial text data on a 0-100 scale
"""

import os
import torch
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from transformers import AutoTokenizer, AutoModel
import re
from pathlib import Path

# Conditional import for PEFT with fallback
try:
    from peft import PeftModel
    PEFT_AVAILABLE = True
    print("✅ PEFT library available")
except ImportError as e:
    print(f"⚠️ PEFT library not available: {e}")
    print("📝 Will use base model only")
    PEFT_AVAILABLE = False
    PeftModel = None

# Set environment variables for model loading (force mirror usage)
os.environ['HF_HOME'] = "/root/autodl-tmp/huggingface_cache"
os.environ['HF_ENDPOINT'] = "https://hf-mirror.com"
os.environ['HF_HUB_DISABLE_TELEMETRY'] = "1"
os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = "1000"
# Force all HuggingFace downloads to use mirror


class FinancialSentimentAnalyzer:
    """Financial sentiment analyzer using FinGPT model with LoRA adapter"""
    
    def __init__(self, base_model_name="THUDM/chatglm2-6b", 
                 adapter_model_name="FinGPT/fingpt-mt_chatglm2-6b_lora"):
        """
        Initialize the sentiment analyzer
        
        Args:
            base_model_name: Base ChatGLM2-6B model name
            adapter_model_name: FinGPT LoRA adapter model name
        """
        self.base_model_name = base_model_name
        self.adapter_model_name = adapter_model_name
        self.tokenizer = None
        self.model = None
        self.device = None
        
    def load_model(self) -> bool:
        """
        Load the FinGPT model with LoRA adapter
        
        Returns:
            bool: Success status
        """
        print(f"🔍 Loading FinGPT model with adapter: {self.adapter_model_name}")
        print(f"🌐 Using mirror source: {os.environ.get('HF_ENDPOINT', 'https://huggingface.co')}")
        
        try:
            # Step 1: Load base model
            print(f"🔄 Loading base model: {self.base_model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.base_model_name,
                trust_remote_code=True
            )
            print("✅ Base tokenizer loaded successfully")
            
            base_model = AutoModel.from_pretrained(
                self.base_model_name,
                trust_remote_code=True,
                device_map='auto',
                torch_dtype=torch.float16
            )
            print("✅ Base model loaded successfully")

            # Step 2: Apply LoRA adapter if available
            if PEFT_AVAILABLE:
                print("🔄 Applying LoRA adapter...")
                try:
                    print(f"🌐 Loading FinGPT adapter: {self.adapter_model_name}")
                    self.model = PeftModel.from_pretrained(
                        base_model, 
                        self.adapter_model_name
                    )
                    self.model = self.model.eval()
                    print("✅ FinGPT model with LoRA adapter loaded successfully")
                except Exception as adapter_error:
                    print(f"⚠️ LoRA adapter loading failed: {adapter_error}")
                    print("📝 Using base model without adapter")
                    self.model = base_model
            else:
                print("⚠️ PEFT not available, using base model only")
                self.model = base_model
            
            # Set device
            self.device = next(self.model.parameters()).device
            print(f"📱 Model running device: {self.device}")
            
            return True
            
        except Exception as e:
            print(f"❌ Model loading failed: {e}")
            # Try to load base model only as fallback
            try:
                print("🔄 Trying to load base model only as fallback...")
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.base_model_name,
                    trust_remote_code=True
                )
                self.model = AutoModel.from_pretrained(
                    self.base_model_name,
                    trust_remote_code=True,
                    device_map='auto',
                    torch_dtype=torch.float16
                )
                self.device = next(self.model.parameters()).device
                print("✅ Base model loaded successfully as fallback")
                return True
            except Exception as fallback_error:
                print(f"❌ Fallback model loading also failed: {fallback_error}")
                return False
    
    def analyze_sentiment(self, text: str) -> float:
        """
        Analyze sentiment of financial text and return score 0-100
        
        Args:
            text: Financial text to analyze
            
        Returns:
            float: Sentiment score from 0 (negative) to 100 (positive)
        """
        if self.model is None or self.tokenizer is None:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        # Create prompt for sentiment analysis
        prompt = f"""As a financial analyst, please analyze the sentiment of the following financial report text and provide a score from 0 to 100:

Scoring criteria:
- 0-20: Very negative (e.g., major losses, debt crisis, regulatory penalties)
- 21-40: Negative (e.g., revenue decline, cost increases, market concerns)
- 41-60: Neutral (e.g., regular operations, stable market)
- 61-80: Positive (e.g., revenue growth, successful new products, market expansion)
- 81-100: Very positive (e.g., significant profits, breakthrough developments, strong growth)

Financial text: {text}

Please provide only the numerical score (0-100):"""

        try:
            # Generate response using the basic chat method
            # Try to handle tokenizer compatibility issues
            response, _ = self.model.chat(self.tokenizer, prompt, history=[])
            
            # Extract numerical score from response
            score = self._extract_score(response)
            
            return score
            
        except Exception as e:
            if "padding_side" in str(e):
                print(f"⚠️ Tokenizer compatibility issue: {e}")
                print("📝 Using fallback sentiment analysis...")
                # Use a simple rule-based fallback for sentiment analysis
                return self._fallback_sentiment_analysis(text)
            else:
                print(f"❌ Sentiment analysis failed: {e}")
                return 50.0  # Return neutral score on error
    
    def _extract_score(self, response: str) -> float:
        """
        Extract numerical score from model response
        
        Args:
            response: Model response text
            
        Returns:
            float: Extracted score
        """
        # Try to find numerical score in response
        numbers = re.findall(r'\b(\d+(?:\.\d+)?)\b', response)
        
        if numbers:
            score = float(numbers[0])
            # Ensure score is within 0-100 range
            score = max(0, min(100, score))
            return score
        
        # If no number found, try to extract from text
        response_lower = response.lower()
        if 'very positive' in response_lower or 'extremely positive' in response_lower:
            return 90.0
        elif 'positive' in response_lower:
            return 70.0
        elif 'neutral' in response_lower:
            return 50.0
        elif 'negative' in response_lower:
            return 30.0
        elif 'very negative' in response_lower or 'extremely negative' in response_lower:
            return 10.0
        
        # Default to neutral if unclear
        return 50.0
    
    def _fallback_sentiment_analysis(self, text: str) -> float:
        """
        Fallback sentiment analysis using simple rule-based approach
        Used when the main model has tokenizer compatibility issues
        
        Args:
            text: Financial text to analyze
            
        Returns:
            float: Sentiment score from 0-100
        """
        text_lower = text.lower()
        
        # Positive indicators
        positive_words = [
            'growth', 'increase', 'profit', 'revenue', 'success', 'strong', 'positive',
            'exceeded', 'outperformed', 'improved', 'better', 'gain', 'rise', 'up',
            'expansion', 'development', 'innovation', 'breakthrough', 'achievement'
        ]
        
        # Negative indicators
        negative_words = [
            'decline', 'decrease', 'loss', 'negative', 'weak', 'poor', 'down',
            'underperformed', 'worse', 'fall', 'drop', 'crisis', 'risk', 'concern',
            'challenge', 'problem', 'issue', 'difficulty', 'uncertainty', 'volatility'
        ]
        
        # Count positive and negative indicators
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        # Calculate sentiment score
        if positive_count > negative_count:
            # More positive indicators
            score = 60 + min(30, positive_count * 5)  # 60-90 range
        elif negative_count > positive_count:
            # More negative indicators
            score = 40 - min(30, negative_count * 5)  # 10-40 range
        else:
            # Balanced or neutral
            score = 50.0
        
        # Ensure score is within 0-100 range
        return max(0.0, min(100.0, score))
    
    def batch_analyze_sentiment(self, texts: List[str]) -> List[float]:
        """
        Analyze sentiment for multiple texts
        
        Args:
            texts: List of financial texts
            
        Returns:
            List[float]: List of sentiment scores
        """
        scores = []
        for i, text in enumerate(texts):
            print(f"📊 Analyzing sentiment {i+1}/{len(texts)}")
            score = self.analyze_sentiment(text)
            scores.append(score)
        
        return scores
    
    def process_financial_reports(self, data_dir: str) -> Dict[str, Dict[str, float]]:
        """
        Process all financial reports in the data directory
        
        Args:
            data_dir: Directory containing financial reports
            
        Returns:
            Dict mapping company -> quarter -> sentiment score
        """
        results = {}
        data_path = Path(data_dir)
        
        if not data_path.exists():
            raise ValueError(f"Data directory not found: {data_dir}")
        
        # Get all company directories
        company_dirs = [d for d in data_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
        
        for company_dir in company_dirs:
            company = company_dir.name
            print(f"📈 Processing {company}...")
            
            results[company] = {}
            
            # Get all cleaned markdown files
            md_files = list(company_dir.glob("*_cleaned.md"))
            
            for md_file in md_files:
                # Extract quarter info from filename
                quarter_info = self._extract_quarter_info(md_file.name)
                if quarter_info:
                    quarter_key = f"{quarter_info['year']}_Q{quarter_info['quarter']}"
                    
                    # Read and analyze the file
                    try:
                        with open(md_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Clean and truncate content for analysis
                        cleaned_content = self._clean_financial_text(content)
                        
                        # Analyze sentiment
                        sentiment_score = self.analyze_sentiment(cleaned_content)
                        results[company][quarter_key] = sentiment_score
                        
                        print(f"  ✅ {quarter_key}: {sentiment_score:.1f}")
                        
                    except Exception as e:
                        print(f"  ❌ Error processing {md_file.name}: {e}")
                        results[company][quarter_key] = 50.0  # Default neutral score
        
        return results
    
    def _extract_quarter_info(self, filename: str) -> Optional[Dict[str, int]]:
        """
        Extract year and quarter information from filename
        
        Args:
            filename: Filename to parse
            
        Returns:
            Dict with year and quarter, or None if not found
        """
        # Pattern: COMPANY_YYYY_QQ_YYYYMMDD_cleaned.md
        pattern = r'_(\d{4})_Q(\d)_'
        match = re.search(pattern, filename)
        
        if match:
            year = int(match.group(1))
            quarter = int(match.group(2))
            return {'year': year, 'quarter': quarter}
        
        return None
    
    def _clean_financial_text(self, text: str, max_length: int = None) -> str:
        """
        Clean financial text for sentiment analysis
        
        Args:
            text: Raw financial text
            max_length: Maximum length to keep (None = no limit)
            
        Returns:
            str: Cleaned text
        """
        # Remove table markers and excessive whitespace
        text = re.sub(r'\[表格:.*?\]', '', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remove headers and very short lines, but keep meaningful content
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Keep lines that are meaningful content
            # Skip empty lines, very short lines, and pure header lines
            if (len(line) > 10 and 
                not line.startswith('=') and 
                not (line.startswith('#') and len(line) < 50)):
                cleaned_lines.append(line)
        
        # Join lines
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Clean up multiple spaces but preserve sentence structure
        cleaned_text = re.sub(r' +', ' ', cleaned_text)
        
        # Optionally truncate
        if max_length and len(cleaned_text) > max_length:
            cleaned_text = cleaned_text[:max_length] + "..."
        
        return cleaned_text


def test_sentiment_analyzer():
    """Test the sentiment analyzer with sample data"""
    print("🚀 Testing Financial Sentiment Analyzer...")
    
    # Initialize analyzer
    analyzer = FinancialSentimentAnalyzer()
    
    # Load model
    if not analyzer.load_model():
        print("❌ Model loading failed")
        return
    
    # Test with sample financial texts
    sample_texts = [
        "The company reported strong quarterly earnings with revenue growth of 25% and improved profit margins.",
        "Economic uncertainty and rising interest rates have negatively impacted market performance.",
        "The new product launch exceeded expectations with strong customer adoption and positive reviews.",
        "Management expressed concerns about supply chain disruptions and increased operational costs."
    ]
    
    print("\n📊 Testing sentiment analysis...")
    for i, text in enumerate(sample_texts, 1):
        score = analyzer.analyze_sentiment(text)
        print(f"Text {i}: {score:.1f}")
        print(f"Content: {text[:100]}...")
        print()
    
    # Test with real financial report
    print("📈 Testing with real financial report...")
    test_file = "/root/quant/data/dogs_of_30_mdna/AAPL/AAPL_2020_Q4_20201226_mdna_cleaned.md"
    
    if os.path.exists(test_file):
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        cleaned_content = analyzer._clean_financial_text(content)
        score = analyzer.analyze_sentiment(cleaned_content)
        
        print(f"Apple Q4 2020 sentiment score: {score:.1f}")
        print(f"Sample content: {cleaned_content[:200]}...")
    
    print("✅ Testing completed!")


if __name__ == "__main__":
    test_sentiment_analyzer()
