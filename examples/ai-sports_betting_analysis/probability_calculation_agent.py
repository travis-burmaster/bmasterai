"""
Probability Calculation Agent for Sports Betting Analysis System

This agent synthesizes results from all other agents to generate final
probability estimates, confidence intervals, and betting recommendations.
"""

import numpy as np
from scipy import stats
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import json
import asyncio

from base_agent import BaseAgent, AgentResult


class BayesianUpdater:
    """Bayesian updating for probability refinement"""
    
    def __init__(self):
        self.prior_alpha = 1.0  # Prior beta distribution parameters
        self.prior_beta = 1.0
    
    def update_probability(self, prior_prob: float, new_evidence: Dict[str, Any]) -> float:
        """Update probability using Bayesian inference"""
        # Convert probability to beta distribution parameters
        alpha = prior_prob * (self.prior_alpha + self.prior_beta - 2) + self.prior_alpha
        beta = (1 - prior_prob) * (self.prior_alpha + self.prior_beta - 2) + self.prior_beta
        
        # Update with new evidence
        evidence_weight = new_evidence.get("weight", 1.0)
        evidence_support = new_evidence.get("support", 0.5)  # 0-1 scale
        
        alpha += evidence_support * evidence_weight
        beta += (1 - evidence_support) * evidence_weight
        
        # Return updated probability
        return alpha / (alpha + beta)
    
    def calculate_confidence_interval(self, alpha: float, beta: float, 
                                    confidence_level: float = 0.95) -> Tuple[float, float]:
        """Calculate confidence interval for beta distribution"""
        lower_percentile = (1 - confidence_level) / 2
        upper_percentile = 1 - lower_percentile
        
        lower_bound = stats.beta.ppf(lower_percentile, alpha, beta)
        upper_bound = stats.beta.ppf(upper_percentile, alpha, beta)
        
        return lower_bound, upper_bound


class ExpectedValueCalculator:
    """Calculate expected value for different betting scenarios"""
    
    def __init__(self):
        self.kelly_fraction_limit = 0.25  # Maximum Kelly fraction to bet
    
    def calculate_expected_value(self, probability: float, odds: float) -> float:
        """
        Calculate expected value of a bet
        
        Args:
            probability: True probability of outcome (0-1)
            odds: Decimal odds offered by bookmaker
        
        Returns:
            Expected value as a percentage
        """
        if probability <= 0 or odds <= 1:
            return -1.0  # Invalid inputs
        
        # Expected value = (probability * (odds - 1)) - (1 - probability)
        expected_value = (probability * (odds - 1)) - (1 - probability)
        return expected_value
    
    def calculate_kelly_criterion(self, probability: float, odds: float) -> float:
        """
        Calculate optimal bet size using Kelly Criterion
        
        Args:
            probability: True probability of outcome (0-1)
            odds: Decimal odds offered by bookmaker
        
        Returns:
            Fraction of bankroll to bet (0-1)
        """
        if probability <= 0 or odds <= 1:
            return 0.0
        
        # Kelly fraction = (bp - q) / b
        # where b = odds - 1, p = probability, q = 1 - probability
        b = odds - 1
        p = probability
        q = 1 - probability
        
        kelly_fraction = (b * p - q) / b
        
        # Apply safety limits
        kelly_fraction = max(0, min(kelly_fraction, self.kelly_fraction_limit))
        
        return kelly_fraction
    
    def analyze_betting_value(self, probabilities: Dict[str, float], 
                            market_odds: Dict[str, float]) -> Dict[str, Any]:
        """Analyze betting value across multiple outcomes"""
        value_analysis = {}
        
        for outcome in probabilities:
            if outcome in market_odds:
                prob = probabilities[outcome]
                odds = market_odds[outcome]
                
                expected_value = self.calculate_expected_value(prob, odds)
                kelly_fraction = self.calculate_kelly_criterion(prob, odds)
                
                # Calculate implied probability from odds
                implied_prob = 1 / odds if odds > 0 else 0
                
                # Calculate edge (difference between true and implied probability)
                edge = prob - implied_prob
                
                value_analysis[outcome] = {
                    "true_probability": prob,
                    "implied_probability": implied_prob,
                    "odds": odds,
                    "expected_value": expected_value,
                    "kelly_fraction": kelly_fraction,
                    "edge": edge,
                    "is_value_bet": expected_value > 0,
                    "confidence_rating": self._calculate_confidence_rating(prob, edge, expected_value)
                }
        
        return value_analysis


    def _calculate_confidence_rating(self, probability: float, edge: float, 
                                   expected_value: float) -> str:
        """Calculate confidence rating for a bet"""
        if expected_value <= 0:
            return "No Value"
        elif edge > 0.1 and expected_value > 0.2:
            return "High Confidence"
        elif edge > 0.05 and expected_value > 0.1:
            return "Medium Confidence"
        elif expected_value > 0:
            return "Low Confidence"
        else:
            return "No Value"


class ProbabilityCalculationAgent(BaseAgent):
    """
    Agent that synthesizes all analysis results into final probability estimates
    and betting recommendations with confidence intervals.
    """
    
    def __init__(self):
        super().__init__("probability_calculation_agent")
        
        self.bayesian_updater = BayesianUpdater()
        self.ev_calculator = ExpectedValueCalculator()
        
        # Weights for different analysis sources
        self.source_weights = {
            "statistical_analysis": 0.4,
            "market_analysis": 0.3,
            "news_sentiment": 0.2,
            "historical_performance": 0.1
        }
    
    def extract_probabilities_from_statistical_analysis(self, stats_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract probabilities from statistical analysis results"""
        if "final_probabilities" in stats_data:
            return stats_data["final_probabilities"]
        
        # Fallback extraction
        return {
            "team1_win": stats_data.get("team1_win_probability", 0.5),
            "team2_win": stats_data.get("team2_win_probability", 0.5),
            "tie": stats_data.get("tie_probability", 0.0)
        }
    
    def extract_market_sentiment(self, market_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract market sentiment and line movement indicators"""
        # Mock implementation - in real system would analyze actual market data
        return {
            "sharp_money_indicator": 0.6,  # 0-1 scale
            "public_betting_percentage": 0.7,  # Percentage on favorite
            "line_movement_strength": 0.3,  # Strength of line movement
            "market_efficiency_score": 0.8  # How efficient the market appears
        }
    
    def extract_news_sentiment(self, news_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract sentiment scores from news analysis"""
        if "error" in news_data:
            return {"sentiment_score": 0.5, "confidence": 0.3}
        
        # Analyze news results for sentiment
        results = news_data.get("results", [])
        if not results:
            return {"sentiment_score": 0.5, "confidence": 0.3}
        
        # Simple sentiment analysis based on content
        positive_keywords = ["strong", "healthy", "confident", "advantage", "momentum"]
        negative_keywords = ["injured", "struggling", "weak", "concern", "doubt"]
        
        sentiment_scores = []
        for article in results:
            content = article.get("content", "").lower()
            positive_count = sum(1 for word in positive_keywords if word in content)
            negative_count = sum(1 for word in negative_keywords if word in content)
            
            if positive_count + negative_count > 0:
                sentiment = positive_count / (positive_count + negative_count)
            else:
                sentiment = 0.5
            
            sentiment_scores.append(sentiment)
        
        avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0.5
        confidence = min(0.8, len(sentiment_scores) / 10)  # More articles = higher confidence
        
        return {
            "sentiment_score": avg_sentiment,
            "confidence": confidence,
            "articles_analyzed": len(sentiment_scores)
        }
    
    def synthesize_probabilities(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize probabilities from all agent results"""
        self.log_thinking_step(
            step_type="probability_synthesis",
            reasoning="Synthesizing probabilities from all agent analyses",
            confidence=0.8
        )
        
        # Extract base probabilities from statistical analysis
        stats_data = agent_results.get("statistical_analysis", {}).get("data", {})
        base_probabilities = self.extract_probabilities_from_statistical_analysis(stats_data)
        
        self.log_thinking_step(
            step_type="base_probabilities",
            reasoning="Extracted base probabilities from statistical analysis",
            confidence=0.8,
            data={"base_probabilities": base_probabilities}
        )
        
        # Extract market sentiment
        market_data = agent_results.get("market_analysis", {}).get("data", {})
        market_sentiment = self.extract_market_sentiment(market_data)
        
        # Extract news sentiment
        news_data = agent_results.get("news_sentiment", {}).get("data", {})
        news_sentiment = self.extract_news_sentiment(news_data)
        
        self.log_thinking_step(
            step_type="sentiment_analysis",
            reasoning="Analyzed market and news sentiment",
            confidence=0.7,
            data={
                "market_sentiment": market_sentiment,
                "news_sentiment": news_sentiment
            }
        )
        
        # Apply Bayesian updating
        updated_probabilities = {}
        
        for outcome in base_probabilities:
            base_prob = base_probabilities[outcome]
            
            # Update with news sentiment
            if outcome == "team1_win":
                sentiment_evidence = {
                    "weight": news_sentiment.get("confidence", 0.5),
                    "support": news_sentiment.get("sentiment_score", 0.5)
                }
            elif outcome == "team2_win":
                sentiment_evidence = {
                    "weight": news_sentiment.get("confidence", 0.5),
                    "support": 1.0 - news_sentiment.get("sentiment_score", 0.5)
                }
            else:  # tie
                sentiment_evidence = {
                    "weight": 0.1,
                    "support": 0.1
                }
            
            updated_prob = self.bayesian_updater.update_probability(base_prob, sentiment_evidence)
            updated_probabilities[outcome] = updated_prob
        
        # Normalize probabilities to sum to 1
        total_prob = sum(updated_probabilities.values())
        if total_prob > 0:
            for outcome in updated_probabilities:
                updated_probabilities[outcome] /= total_prob
        
        return {
            "base_probabilities": base_probabilities,
            "updated_probabilities": updated_probabilities,
            "market_sentiment": market_sentiment,
            "news_sentiment": news_sentiment
        }
    
    def calculate_confidence_intervals(self, probabilities: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        """Calculate confidence intervals for probability estimates"""
        confidence_intervals = {}
        
        for outcome, prob in probabilities.items():
            # Convert probability to beta distribution parameters
            # Using method of moments with assumed variance
            variance = prob * (1 - prob) * 0.1  # Assumed 10% relative variance
            
            if variance > 0:
                # Method of moments for beta distribution
                alpha = prob * ((prob * (1 - prob)) / variance - 1)
                beta = (1 - prob) * ((prob * (1 - prob)) / variance - 1)
                
                # Ensure parameters are positive
                alpha = max(0.1, alpha)
                beta = max(0.1, beta)
                
                lower_bound, upper_bound = self.bayesian_updater.calculate_confidence_interval(alpha, beta)
            else:
                lower_bound = upper_bound = prob
            
            confidence_intervals[outcome] = {
                "point_estimate": prob,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
                "confidence_width": upper_bound - lower_bound
            }
        
        return confidence_intervals
    
    def generate_betting_recommendations(self, probability_analysis: Dict[str, Any],
                                       mock_odds: Dict[str, float] = None) -> Dict[str, Any]:
        """Generate betting recommendations with expected value analysis"""
        
        # Use mock odds for demonstration
        if mock_odds is None:
            mock_odds = {
                "team1_win": 2.1,  # Decimal odds
                "team2_win": 1.8,
                "tie": 8.0
            }
        
        self.log_thinking_step(
            step_type="betting_recommendations",
            reasoning="Generating betting recommendations with expected value analysis",
            confidence=0.8,
            data={"mock_odds": mock_odds}
        )
        
        probabilities = probability_analysis["updated_probabilities"]
        
        # Calculate expected values and Kelly fractions
        value_analysis = self.ev_calculator.analyze_betting_value(probabilities, mock_odds)
        
        # Generate recommendations
        recommendations = []
        
        for outcome, analysis in value_analysis.items():
            if analysis["is_value_bet"] and analysis["expected_value"] > 0.05:  # 5% minimum EV
                recommendations.append({
                    "outcome": outcome,
                    "recommendation": "BET",
                    "confidence": analysis["confidence_rating"],
                    "expected_value": analysis["expected_value"],
                    "suggested_stake": analysis["kelly_fraction"],
                    "reasoning": f"Positive expected value of {analysis['expected_value']:.1%} with {analysis['edge']:.1%} edge over market"
                })
            else:
                recommendations.append({
                    "outcome": outcome,
                    "recommendation": "PASS",
                    "confidence": "No Value",
                    "expected_value": analysis["expected_value"],
                    "suggested_stake": 0.0,
                    "reasoning": f"Negative expected value of {analysis['expected_value']:.1%}"
                })
        
        # Sort by expected value
        recommendations.sort(key=lambda x: x["expected_value"], reverse=True)
        
        return {
            "value_analysis": value_analysis,
            "recommendations": recommendations,
            "best_bet": recommendations[0] if recommendations else None,
            "total_opportunities": sum(1 for r in recommendations if r["recommendation"] == "BET")
        }
    
    def calculate_overall_confidence(self, agent_results: Dict[str, Any]) -> float:
        """Calculate overall confidence in the analysis"""
        confidences = []
        
        for agent_name, result in agent_results.items():
            if isinstance(result, dict) and "confidence" in result:
                confidences.append(result["confidence"])
        
        if not confidences:
            return 0.5
        
        # Use harmonic mean to be conservative
        harmonic_mean = len(confidences) / sum(1/c for c in confidences if c > 0)
        
        return min(0.95, harmonic_mean)  # Cap at 95%
    
    async def run_async(self) -> AgentResult:
        """Main execution method for probability calculation"""
        task_id = self.start_task("Comprehensive probability calculation and betting analysis")
        
        try:
            # For demonstration, create mock agent results
            # In real implementation, this would receive results from other agents
            mock_agent_results = {
                "statistical_analysis": {
                    "success": True,
                    "confidence": 0.8,
                    "data": {
                        "final_probabilities": {
                            "team1_win": 0.55,
                            "team2_win": 0.42,
                            "tie": 0.03
                        },
                        "model_confidence": 0.8
                    }
                },
                "market_analysis": {
                    "success": True,
                    "confidence": 0.7,
                    "data": {
                        "line_movement": "stable",
                        "public_betting": 0.65
                    }
                },
                "news_sentiment": {
                    "success": True,
                    "confidence": 0.6,
                    "data": {
                        "results": [
                            {"content": "Team looks strong and healthy going into the game"},
                            {"content": "Key player injury concerns for the visiting team"}
                        ]
                    }
                }
            }
            
            self.log_thinking_step(
                step_type="analysis_start",
                reasoning="Starting probability calculation with agent results",
                confidence=0.8,
                data={"available_agents": list(mock_agent_results.keys())}
            )
            
            # Synthesize probabilities
            probability_analysis = self.synthesize_probabilities(mock_agent_results)
            
            # Calculate confidence intervals
            confidence_intervals = self.calculate_confidence_intervals(
                probability_analysis["updated_probabilities"]
            )
            
            # Generate betting recommendations
            betting_recommendations = self.generate_betting_recommendations(probability_analysis)
            
            # Calculate overall confidence
            overall_confidence = self.calculate_overall_confidence(mock_agent_results)
            
            self.log_thinking_step(
                step_type="analysis_complete",
                reasoning="Probability calculation completed successfully",
                confidence=overall_confidence,
                data={
                    "final_probabilities": probability_analysis["updated_probabilities"],
                    "best_bet": betting_recommendations["best_bet"],
                    "total_opportunities": betting_recommendations["total_opportunities"]
                }
            )
            
            final_results = {
                "probability_analysis": probability_analysis,
                "confidence_intervals": confidence_intervals,
                "betting_recommendations": betting_recommendations,
                "overall_confidence": overall_confidence,
                "analysis_summary": {
                    "most_likely_outcome": max(probability_analysis["updated_probabilities"], 
                                             key=probability_analysis["updated_probabilities"].get),
                    "highest_value_bet": betting_recommendations["best_bet"],
                    "recommendation_count": len(betting_recommendations["recommendations"]),
                    "value_opportunities": betting_recommendations["total_opportunities"]
                }
            }
            
            return self.complete_task(
                task_id=task_id,
                success=True,
                result_data=final_results,
                confidence=overall_confidence
            )
        
        except Exception as e:
            return self.complete_task(
                task_id=task_id,
                success=False,
                result_data={},
                confidence=0.0,
                error_message=str(e)
            )

