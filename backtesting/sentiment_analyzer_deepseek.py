#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Financial Sentiment Analyzer using DeepSeek API
Provides sentiment scoring for financial text data on a 0-100 scale
"""

import os
import requests
import json
import time
from typing import Dict, List, Optional, Tuple
import re
from pathlib import Path

# =============================================================================
# DeepSeek API Configuration - 直接在这里设置你的API密钥
# =============================================================================

# 在这里设置你的DeepSeek API密钥
DEEPSEEK_API_KEY = "sk-5d010895003640bc936d09aec5790723"  # 替换为你的实际API密钥
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"


class DeepSeekSentimentAnalyzer:
    """Financial sentiment analyzer using DeepSeek API"""
    
    def __init__(self, api_key: str = None, base_url: str = "https://api.deepseek.com/v1"):
        """
        Initialize the DeepSeek sentiment analyzer
        
        Args:
            api_key: DeepSeek API key (if None, will try to get from environment or use default)
            base_url: DeepSeek API base URL
        """
        # Use API key from parameter or from the global variable above
        self.api_key = api_key or DEEPSEEK_API_KEY
        self.base_url = base_url or DEEPSEEK_BASE_URL
        self.model = "deepseek-chat"
        
        if not self.api_key or self.api_key == "your-deepseek-api-key-here":
            raise ValueError("DeepSeek API key is required. Please edit the DEEPSEEK_API_KEY variable at the top of this file.")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
        
        print("✅ DeepSeek API sentiment analyzer initialized")
        
        # Cache for sentiment analysis results
        self.sentiment_cache = {}
        self.cache_file = None
    
    def process_financial_reports(self, data_dir: str, cache_file: str = None) -> Dict[str, Dict[str, float]]:
        """
        Process all financial reports in the data directory
        
        Args:
            data_dir: Directory containing financial reports
            cache_file: Optional cache file to save/load results
            
        Returns:
            Dict mapping company -> quarter -> sentiment score
        """
        self.cache_file = cache_file
        
        # Try to load from cache first
        if cache_file and os.path.exists(cache_file):
            try:
                import json
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                print(f"✅ Loaded sentiment cache from {cache_file}")
                return cached_data
            except Exception as e:
                print(f"⚠️ Failed to load cache: {e}")
        
        sentiment_data = {}
        
        # Get all company directories
        data_path = Path(data_dir)
        if not data_path.exists():
            print(f"❌ Data directory not found: {data_dir}")
            return sentiment_data
        
        company_dirs = [d for d in data_path.iterdir() if d.is_dir()]
        print(f"📊 Processing {len(company_dirs)} companies...")
        
        for company_dir in company_dirs:
            company = company_dir.name
            sentiment_data[company] = {}
            
            # Find all cleaned MDNA files
            cleaned_files = list(company_dir.glob("*_mdna_cleaned.md"))
            
            for file_path in cleaned_files:
                try:
                    # Extract quarter from filename
                    filename = file_path.stem
                    if "_mdna_cleaned" in filename:
                        # Extract year and quarter from filename like "AAPL_2020_Q4_20201226_mdna_cleaned"
                        parts = filename.split('_')
                        if len(parts) >= 3:
                            year = parts[1]
                            quarter = parts[2]
                            quarter_key = f"{year}_{quarter}"
                        else:
                            continue
                    else:
                        continue
                    
                    # Read and analyze the file
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if content.strip():
                        sentiment_score = self.analyze_sentiment(content)
                        sentiment_data[company][quarter_key] = sentiment_score
                        print(f"  {company} {quarter_key}: {sentiment_score:.1f}")
                    
                except Exception as e:
                    print(f"⚠️ Error processing {file_path}: {e}")
                    continue
        
        print(f"✅ Processed sentiment data for {len(sentiment_data)} companies")
        
        # Save to cache if cache file is provided
        if cache_file:
            try:
                import json
                os.makedirs(os.path.dirname(cache_file), exist_ok=True)
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(sentiment_data, f, indent=2, ensure_ascii=False)
                print(f"✅ Saved sentiment cache to {cache_file}")
            except Exception as e:
                print(f"⚠️ Failed to save cache: {e}")
        
        return sentiment_data
    
    def _rate_limit(self):
        """Apply rate limiting to avoid hitting API limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        
        self.last_request_time = time.time()
    
    def _clean_financial_text(self, text: str) -> str:
        """
        Clean and preprocess financial text for sentiment analysis
        
        Args:
            text: Raw financial text
            
        Returns:
            Cleaned text suitable for sentiment analysis
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might confuse the model
        text = re.sub(r'[^\w\s.,!?;:()\-%$]', '', text)
        
        # Remove very short sentences (likely noise)
        sentences = text.split('.')
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        text = '. '.join(sentences)
        
        # Limit text length to avoid token limits
        max_length = 4000  # Conservative limit for DeepSeek
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        return text.strip()
    
    def _create_sentiment_prompt(self, text: str) -> str:
        """
        Create a prompt for sentiment analysis
        
        Args:
            text: Financial text to analyze
            
        Returns:
            Formatted prompt for the API
        """
        prompt = f"""You are a financial sentiment analysis expert. Analyze the following financial text and provide a sentiment score from 0 to 100.

Scoring Guidelines:
- 0-20: Very negative sentiment (severe losses, major problems, bankruptcy risk)
- 21-40: Negative sentiment (declining performance, challenges, concerns)
- 41-60: Neutral sentiment (mixed results, stable performance, no clear trend)
- 61-80: Positive sentiment (good performance, growth, improvements)
- 81-100: Very positive sentiment (excellent results, strong growth, major successes)

Consider factors like:
- Revenue and profit trends
- Market performance
- Management outlook
- Competitive position
- Risk factors
- Growth prospects

Financial Text:
{text}

Please provide ONLY a single number between 0 and 100 representing the overall sentiment. Do not include any explanation or additional text."""

        return prompt
    
    def analyze_sentiment(self, text: str) -> float:
        """
        Analyze sentiment of financial text using DeepSeek API
        
        Args:
            text: Financial text to analyze
            
        Returns:
            Sentiment score from 0-100 (float)
        """
        if not text or not isinstance(text, str):
            return 50.0  # Neutral score for invalid input
        
        # Clean the text
        cleaned_text = self._clean_financial_text(text)
        
        if not cleaned_text:
            return 50.0  # Neutral score for empty text
        
        # Create prompt
        prompt = self._create_sentiment_prompt(cleaned_text)
        
        # Prepare API request
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,  # Low temperature for consistent results
            "max_tokens": 10,    # We only need a number
            "stream": False
        }
        
        try:
            # Apply rate limiting
            self._rate_limit()
            
            # Make API request
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content'].strip()
                    
                    # Extract numeric score
                    score = self._extract_sentiment_score(content)
                    return score
                else:
                    print(f"⚠️ Unexpected API response format: {result}")
                    return 50.0
            else:
                print(f"❌ API request failed with status {response.status_code}: {response.text}")
                return 50.0
                
        except requests.exceptions.Timeout:
            print("⏰ API request timed out, using neutral score")
            return 50.0
        except requests.exceptions.RequestException as e:
            print(f"❌ API request failed: {e}")
            return 50.0
        except Exception as e:
            print(f"❌ Unexpected error in sentiment analysis: {e}")
            return 50.0
    
    def _extract_sentiment_score(self, content: str) -> float:
        """
        Extract sentiment score from API response
        
        Args:
            content: Raw content from API response
            
        Returns:
            Extracted sentiment score (0-100)
        """
        try:
            # Try to extract number from content
            import re
            numbers = re.findall(r'\d+(?:\.\d+)?', content)
            
            if numbers:
                score = float(numbers[0])
                # Ensure score is within valid range
                score = max(0, min(100, score))
                return score
            else:
                print(f"⚠️ Could not extract number from: {content}")
                return 50.0
                
        except (ValueError, IndexError) as e:
            print(f"⚠️ Error extracting score from '{content}': {e}")
            return 50.0
    
    def analyze_batch(self, texts: List[str]) -> List[float]:
        """
        Analyze sentiment for multiple texts
        
        Args:
            texts: List of financial texts to analyze
            
        Returns:
            List of sentiment scores (0-100)
        """
        scores = []
        
        print(f"📊 Analyzing sentiment for {len(texts)} texts using DeepSeek API...")
        
        for i, text in enumerate(texts):
            if i % 10 == 0:
                print(f"  Progress: {i}/{len(texts)}")
            
            score = self.analyze_sentiment(text)
            scores.append(score)
        
        print(f"✅ Completed sentiment analysis for {len(texts)} texts")
        return scores
    
    def test_api_connection(self) -> bool:
        """
        Test if the API connection is working
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            test_prompt = "Test message"
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": test_prompt}],
                "max_tokens": 5
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ DeepSeek API connection successful")
                return True
            else:
                print(f"❌ DeepSeek API connection failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ DeepSeek API connection test failed: {e}")
            return False


# Example usage and testing
if __name__ == "__main__":
    # Test the analyzer
    analyzer = DeepSeekSentimentAnalyzer()
    
    # Test API connection
    if analyzer.test_api_connection():
        # Test with sample financial text
        sample_texts = [
            "Company reported strong quarterly earnings with revenue growth of 25% and improved profit margins.",
            "Economic uncertainty and rising interest rates have negatively impacted market performance.",
            "The new product launch exceeded expectations with strong customer adoption and positive reviews."
        ]
        
        print("\n📈 Testing sentiment analysis...")
        for i, text in enumerate(sample_texts, 1):
            score = analyzer.analyze_sentiment(text)
            print(f"Text {i}: {score:.1f}/100")
            print(f"Content: {text[:60]}...")
            print()
    else:
        print("❌ API connection failed. Please check your API key and network connection.")
