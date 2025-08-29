"""
Statistical Analysis Agent for Sports Betting Analysis System

This agent implements sophisticated statistical models including:
- Poisson distribution models for scoring predictions
- Elo rating systems for team strength assessment
- Monte Carlo simulations for probability calculations
- Machine learning models for pattern recognition
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import poisson, norm
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import json
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
import asyncio

from base_agent import BaseAgent, AgentResult


class EloRatingSystem:
    """Elo rating system for team strength assessment"""
    
    def __init__(self, k_factor: float = 32, initial_rating: float = 1500):
        self.k_factor = k_factor
        self.initial_rating = initial_rating
        self.ratings = {}
    
    def get_rating(self, team: str) -> float:
        """Get current Elo rating for a team"""
        return self.ratings.get(team, self.initial_rating)
    
    def update_ratings(self, team1: str, team2: str, score1: int, score2: int):
        """Update Elo ratings based on game result"""
        rating1 = self.get_rating(team1)
        rating2 = self.get_rating(team2)
        
        # Calculate expected scores
        expected1 = 1 / (1 + 10 ** ((rating2 - rating1) / 400))
        expected2 = 1 / (1 + 10 ** ((rating1 - rating2) / 400))
        
        # Determine actual scores (1 for win, 0.5 for tie, 0 for loss)
        if score1 > score2:
            actual1, actual2 = 1, 0
        elif score1 < score2:
            actual1, actual2 = 0, 1
        else:
            actual1, actual2 = 0.5, 0.5
        
        # Update ratings
        new_rating1 = rating1 + self.k_factor * (actual1 - expected1)
        new_rating2 = rating2 + self.k_factor * (actual2 - expected2)
        
        self.ratings[team1] = new_rating1
        self.ratings[team2] = new_rating2
        
        return new_rating1, new_rating2
    
    def predict_win_probability(self, team1: str, team2: str) -> Tuple[float, float]:
        """Predict win probabilities for both teams"""
        rating1 = self.get_rating(team1)
        rating2 = self.get_rating(team2)
        
        prob1 = 1 / (1 + 10 ** ((rating2 - rating1) / 400))
        prob2 = 1 - prob1
        
        return prob1, prob2


class PoissonScoringModel:
    """Poisson distribution model for predicting game scores"""
    
    def __init__(self):
        self.team_offensive_strength = {}
        self.team_defensive_strength = {}
        self.league_average_scoring = 24.0  # Default for NFL
    
    def calculate_team_strengths(self, historical_data: List[Dict[str, Any]]):
        """Calculate offensive and defensive strengths from historical data"""
        team_scores = {}
        team_allowed = {}
        
        for game in historical_data:
            home_team = game.get('home_team')
            away_team = game.get('away_team')
            home_score = game.get('home_score', 0)
            away_score = game.get('away_score', 0)
            
            if home_team and away_team:
                # Track scores for and against
                if home_team not in team_scores:
                    team_scores[home_team] = []
                    team_allowed[home_team] = []
                if away_team not in team_scores:
                    team_scores[away_team] = []
                    team_allowed[away_team] = []
                
                team_scores[home_team].append(home_score)
                team_allowed[home_team].append(away_score)
                team_scores[away_team].append(away_score)
                team_allowed[away_team].append(home_score)
        
        # Calculate strengths relative to league average
        for team in team_scores:
            if team_scores[team]:
                avg_scored = np.mean(team_scores[team])
                avg_allowed = np.mean(team_allowed[team])
                
                self.team_offensive_strength[team] = avg_scored / self.league_average_scoring
                self.team_defensive_strength[team] = self.league_average_scoring / avg_allowed
    
    def predict_score_distribution(self, team1: str, team2: str) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Predict score distributions for both teams using Poisson model"""
        # Get team strengths (default to 1.0 if not available)
        team1_offense = self.team_offensive_strength.get(team1, 1.0)
        team1_defense = self.team_defensive_strength.get(team1, 1.0)
        team2_offense = self.team_offensive_strength.get(team2, 1.0)
        team2_defense = self.team_defensive_strength.get(team2, 1.0)
        
        # Calculate expected scores
        team1_expected = self.league_average_scoring * team1_offense * team2_defense
        team2_expected = self.league_average_scoring * team2_offense * team1_defense
        
        # Generate Poisson distributions
        team1_dist = {}
        team2_dist = {}
        
        for score in range(0, 50):  # Reasonable score range
            team1_dist[score] = poisson.pmf(score, team1_expected)
            team2_dist[score] = poisson.pmf(score, team2_expected)
        
        return team1_dist, team2_dist
    
    def calculate_game_probabilities(self, team1: str, team2: str) -> Dict[str, float]:
        """Calculate win/loss/tie probabilities"""
        team1_dist, team2_dist = self.predict_score_distribution(team1, team2)
        
        team1_win_prob = 0.0
        team2_win_prob = 0.0
        tie_prob = 0.0
        
        for score1 in team1_dist:
            for score2 in team2_dist:
                joint_prob = team1_dist[score1] * team2_dist[score2]
                
                if score1 > score2:
                    team1_win_prob += joint_prob
                elif score2 > score1:
                    team2_win_prob += joint_prob
                else:
                    tie_prob += joint_prob
        
        return {
            "team1_win": team1_win_prob,
            "team2_win": team2_win_prob,
            "tie": tie_prob
        }


class MonteCarloSimulator:
    """Monte Carlo simulation for complex scenario modeling"""
    
    def __init__(self, num_simulations: int = 10000):
        self.num_simulations = num_simulations
    
    def simulate_game(self, team1_params: Dict[str, float], team2_params: Dict[str, float],
                     external_factors: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Simulate a game multiple times with various parameters
        
        Args:
            team1_params: Parameters for team 1 (mean_score, std_score, etc.)
            team2_params: Parameters for team 2 (mean_score, std_score, etc.)
            external_factors: Weather, injuries, etc. impact factors
        """
        external_factors = external_factors or {}
        
        team1_wins = 0
        team2_wins = 0
        ties = 0
        
        team1_scores = []
        team2_scores = []
        
        for _ in range(self.num_simulations):
            # Generate random scores based on normal distribution
            team1_score = max(0, np.random.normal(
                team1_params.get('mean_score', 24),
                team1_params.get('std_score', 7)
            ))
            
            team2_score = max(0, np.random.normal(
                team2_params.get('mean_score', 24),
                team2_params.get('std_score', 7)
            ))
            
            # Apply external factors
            weather_impact = external_factors.get('weather_impact', 0)
            injury_impact_team1 = external_factors.get('injury_impact_team1', 0)
            injury_impact_team2 = external_factors.get('injury_impact_team2', 0)
            
            team1_score *= (1 + weather_impact + injury_impact_team1)
            team2_score *= (1 + weather_impact + injury_impact_team2)
            
            team1_scores.append(team1_score)
            team2_scores.append(team2_score)
            
            # Determine winner
            if team1_score > team2_score:
                team1_wins += 1
            elif team2_score > team1_score:
                team2_wins += 1
            else:
                ties += 1
        
        return {
            "team1_win_probability": team1_wins / self.num_simulations,
            "team2_win_probability": team2_wins / self.num_simulations,
            "tie_probability": ties / self.num_simulations,
            "team1_avg_score": np.mean(team1_scores),
            "team2_avg_score": np.mean(team2_scores),
            "team1_score_std": np.std(team1_scores),
            "team2_score_std": np.std(team2_scores),
            "simulations_run": self.num_simulations
        }


class StatisticalAnalysisAgent(BaseAgent):
    """
    Agent that performs comprehensive statistical analysis for sports betting
    """
    
    def __init__(self):
        super().__init__("statistical_analysis_agent")
        
        # Initialize statistical models
        self.elo_system = EloRatingSystem()
        self.poisson_model = PoissonScoringModel()
        self.monte_carlo = MonteCarloSimulator()
        
        # Machine learning models
        self.ml_models = {
            "win_predictor": RandomForestRegressor(n_estimators=100, random_state=42),
            "score_predictor": RandomForestRegressor(n_estimators=100, random_state=42)
        }
        
        self.scaler = StandardScaler()
        self.models_trained = False
    
    def extract_team_names(self, game_data: Dict[str, Any]) -> Tuple[str, str]:
        """Extract team names from various data formats"""
        # Try different possible formats
        if "home_team" in game_data and "away_team" in game_data:
            return game_data["home_team"], game_data["away_team"]
        
        # Try to extract from odds data
        odds_data = game_data.get("odds", {})
        if isinstance(odds_data, list) and len(odds_data) > 0:
            game = odds_data[0]
            return game.get("home_team", "Team A"), game.get("away_team", "Team B")
        
        # Default fallback
        return "Team A", "Team B"
    
    def generate_mock_historical_data(self, team1: str, team2: str) -> List[Dict[str, Any]]:
        """Generate mock historical data for demonstration"""
        historical_data = []
        
        # Generate 20 games of mock data for each team
        for i in range(20):
            # Team 1 games
            historical_data.append({
                "home_team": team1,
                "away_team": f"Opponent_{i}",
                "home_score": np.random.poisson(24),
                "away_score": np.random.poisson(20),
                "date": (datetime.now() - timedelta(days=i*7)).isoformat()
            })
            
            # Team 2 games
            historical_data.append({
                "home_team": team2,
                "away_team": f"Opponent_{i+20}",
                "home_score": np.random.poisson(22),
                "away_score": np.random.poisson(21),
                "date": (datetime.now() - timedelta(days=i*7)).isoformat()
            })
        
        return historical_data
    
    async def analyze_team_performance(self, team_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze team performance metrics"""
        self.log_thinking_step(
            step_type="team_performance_analysis",
            reasoning="Analyzing team performance from available data",
            confidence=0.7
        )
        
        # Extract team statistics if available
        teams_data = team_data.get("teams", {}).get("items", [])
        
        team_analysis = {}
        
        for team in teams_data:
            team_name = team.get("displayName", "Unknown Team")
            
            # Extract basic stats
            record = team.get("record", {}).get("items", [{}])[0].get("stats", [])
            wins = record[0].get("value", 0) if len(record) > 0 else 0
            losses = record[1].get("value", 0) if len(record) > 1 else 0
            
            # Extract advanced stats
            statistics = team.get("statistics", [])
            stats_dict = {}
            for stat in statistics:
                stats_dict[stat.get("name", "")] = stat.get("value", 0)
            
            team_analysis[team_name] = {
                "wins": wins,
                "losses": losses,
                "win_percentage": wins / (wins + losses) if (wins + losses) > 0 else 0.5,
                "points_per_game": stats_dict.get("pointsPerGame", 24.0),
                "points_allowed_per_game": stats_dict.get("pointsAllowedPerGame", 24.0),
                "offensive_efficiency": stats_dict.get("pointsPerGame", 24.0) / 24.0,
                "defensive_efficiency": 24.0 / stats_dict.get("pointsAllowedPerGame", 24.0)
            }
        
        return team_analysis
    
    async def run_elo_analysis(self, team1: str, team2: str, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run Elo rating analysis"""
        self.log_thinking_step(
            step_type="elo_analysis",
            reasoning=f"Running Elo rating analysis for {team1} vs {team2}",
            confidence=0.8
        )
        
        # Update Elo ratings with historical data
        for game in historical_data:
            home_team = game.get("home_team")
            away_team = game.get("away_team")
            home_score = game.get("home_score", 0)
            away_score = game.get("away_score", 0)
            
            if home_team and away_team:
                self.elo_system.update_ratings(home_team, away_team, home_score, away_score)
        
        # Get current ratings and predictions
        team1_rating = self.elo_system.get_rating(team1)
        team2_rating = self.elo_system.get_rating(team2)
        team1_win_prob, team2_win_prob = self.elo_system.predict_win_probability(team1, team2)
        
        return {
            "team1_elo_rating": team1_rating,
            "team2_elo_rating": team2_rating,
            "team1_win_probability": team1_win_prob,
            "team2_win_probability": team2_win_prob,
            "rating_difference": abs(team1_rating - team2_rating),
            "confidence": min(0.9, abs(team1_rating - team2_rating) / 400)
        }
    
    async def run_poisson_analysis(self, team1: str, team2: str, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run Poisson distribution analysis"""
        self.log_thinking_step(
            step_type="poisson_analysis",
            reasoning=f"Running Poisson scoring analysis for {team1} vs {team2}",
            confidence=0.8
        )
        
        # Calculate team strengths
        self.poisson_model.calculate_team_strengths(historical_data)
        
        # Get score distributions and probabilities
        team1_dist, team2_dist = self.poisson_model.predict_score_distribution(team1, team2)
        game_probabilities = self.poisson_model.calculate_game_probabilities(team1, team2)
        
        # Calculate expected scores
        team1_expected = sum(score * prob for score, prob in team1_dist.items())
        team2_expected = sum(score * prob for score, prob in team2_dist.items())
        
        return {
            "team1_expected_score": team1_expected,
            "team2_expected_score": team2_expected,
            "game_probabilities": game_probabilities,
            "total_expected_score": team1_expected + team2_expected,
            "score_difference_expected": abs(team1_expected - team2_expected),
            "model_confidence": 0.75
        }
    
    async def run_monte_carlo_analysis(self, team1: str, team2: str, team_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Run Monte Carlo simulation analysis"""
        self.log_thinking_step(
            step_type="monte_carlo_analysis",
            reasoning=f"Running Monte Carlo simulation for {team1} vs {team2}",
            confidence=0.8
        )
        
        # Extract team parameters
        team1_stats = team_analysis.get(team1, {})
        team2_stats = team_analysis.get(team2, {})
        
        team1_params = {
            "mean_score": team1_stats.get("points_per_game", 24.0),
            "std_score": 7.0  # Default standard deviation
        }
        
        team2_params = {
            "mean_score": team2_stats.get("points_per_game", 24.0),
            "std_score": 7.0
        }
        
        # Run simulation
        simulation_results = self.monte_carlo.simulate_game(team1_params, team2_params)
        
        return simulation_results
    
    async def synthesize_statistical_analysis(self, elo_results: Dict[str, Any], 
                                            poisson_results: Dict[str, Any],
                                            monte_carlo_results: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize results from all statistical models"""
        self.log_thinking_step(
            step_type="statistical_synthesis",
            reasoning="Synthesizing results from all statistical models",
            confidence=0.9
        )
        
        # Weight different models based on their strengths
        elo_weight = 0.3
        poisson_weight = 0.4
        monte_carlo_weight = 0.3
        
        # Calculate weighted probabilities
        team1_win_prob = (
            elo_results["team1_win_probability"] * elo_weight +
            poisson_results["game_probabilities"]["team1_win"] * poisson_weight +
            monte_carlo_results["team1_win_probability"] * monte_carlo_weight
        )
        
        team2_win_prob = (
            elo_results["team2_win_probability"] * elo_weight +
            poisson_results["game_probabilities"]["team2_win"] * poisson_weight +
            monte_carlo_results["team2_win_probability"] * monte_carlo_weight
        )
        
        # Calculate confidence based on model agreement
        model_agreement = 1.0 - abs(
            elo_results["team1_win_probability"] - 
            monte_carlo_results["team1_win_probability"]
        )
        
        return {
            "final_probabilities": {
                "team1_win": team1_win_prob,
                "team2_win": team2_win_prob,
                "tie": 1.0 - team1_win_prob - team2_win_prob
            },
            "expected_scores": {
                "team1": poisson_results["team1_expected_score"],
                "team2": poisson_results["team2_expected_score"]
            },
            "model_confidence": model_agreement,
            "model_weights": {
                "elo": elo_weight,
                "poisson": poisson_weight,
                "monte_carlo": monte_carlo_weight
            },
            "individual_model_results": {
                "elo": elo_results,
                "poisson": poisson_results,
                "monte_carlo": monte_carlo_results
            }
        }
    
    async def run_async(self) -> AgentResult:
        """Main execution method for statistical analysis"""
        task_id = self.start_task("Comprehensive statistical analysis")
        
        try:
            # For demonstration, we'll use mock data
            # In a real implementation, this would come from the data collection agent
            team1, team2 = "Team A", "Team B"
            
            self.log_thinking_step(
                step_type="analysis_start",
                reasoning=f"Starting statistical analysis for {team1} vs {team2}",
                confidence=0.8
            )
            
            # Generate mock data for demonstration
            historical_data = self.generate_mock_historical_data(team1, team2)
            team_analysis = {
                team1: {"points_per_game": 26.5, "points_allowed_per_game": 19.2},
                team2: {"points_per_game": 23.1, "points_allowed_per_game": 22.8}
            }
            
            # Run all statistical analyses in parallel
            elo_task = self.run_elo_analysis(team1, team2, historical_data)
            poisson_task = self.run_poisson_analysis(team1, team2, historical_data)
            monte_carlo_task = self.run_monte_carlo_analysis(team1, team2, team_analysis)
            
            elo_results, poisson_results, monte_carlo_results = await asyncio.gather(
                elo_task, poisson_task, monte_carlo_task
            )
            
            # Synthesize all results
            final_analysis = await self.synthesize_statistical_analysis(
                elo_results, poisson_results, monte_carlo_results
            )
            
            self.log_thinking_step(
                step_type="analysis_complete",
                reasoning="Statistical analysis completed successfully",
                confidence=final_analysis["model_confidence"],
                data={"final_probabilities": final_analysis["final_probabilities"]}
            )
            
            return self.complete_task(
                task_id=task_id,
                success=True,
                result_data=final_analysis,
                confidence=final_analysis["model_confidence"]
            )
        
        except Exception as e:
            return self.complete_task(
                task_id=task_id,
                success=False,
                result_data={},
                confidence=0.0,
                error_message=str(e)
            )

