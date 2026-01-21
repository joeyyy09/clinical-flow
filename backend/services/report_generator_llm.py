"""
LLM-Powered Report Generation Service

This module provides active LLM-based report generation for:
- Site Risk Assessment Reports
- CRA Performance Summaries
- Data Quality Trend Reports
- Executive Dashboard Summaries

Uses Gemini API with structured prompts and fallback to templates.
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

# Try importing Gemini
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


class ReportType(Enum):
    SITE_RISK = "site_risk"
    CRA_PERFORMANCE = "cra_performance"
    DATA_QUALITY = "data_quality"
    EXECUTIVE_SUMMARY = "executive_summary"


@dataclass
class GeneratedReport:
    """Structured report output."""
    report_id: str
    report_type: str
    title: str
    generated_at: str
    executive_summary: str
    sections: List[Dict[str, Any]]
    recommendations: List[str]
    metrics: Dict[str, Any]
    status: str  # "complete", "partial", "error"
    generation_source: str  # "llm", "template"


class LLMReportGenerator:
    """
    LLM-powered report generation with structured clinical insights.
    
    Generates natural language reports by:
    1. Aggregating relevant data from multiple sources
    2. Building context-rich prompts
    3. Using Gemini API for narrative generation
    4. Structuring output for frontend display and PDF export
    """
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.provider = "template"  # Default fallback
        
        if self.api_key and HAS_GEMINI:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-2.0-flash')
                self.provider = "gemini"
                print("[OK] LLM Report Generator: Using Gemini API")
            except Exception as e:
                print(f"[WARN] Gemini init failed: {e}")
        else:
            print("[WARN] LLM Report Generator: Using template fallback")
    
    def generate_site_risk_report(
        self, 
        site_id: str, 
        site_data: Dict[str, Any],
        ml_prediction: Dict[str, Any] = None
    ) -> GeneratedReport:
        """
        Generate comprehensive site risk assessment report.
        
        Args:
            site_id: Site identifier
            site_data: Aggregated site metrics
            ml_prediction: ML model prediction with explainability
            
        Returns:
            GeneratedReport: Structured report with AI narrative
        """
        report_id = f"SRA-{site_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Build context
        context = self._build_site_context(site_id, site_data, ml_prediction)
        
        # Generate narrative
        if self.provider == "gemini":
            narrative = self._generate_site_narrative_llm(context)
        else:
            narrative = self._generate_site_narrative_template(context)
        
        # Structure sections
        sections = [
            {
                "title": "Risk Classification",
                "content": narrative.get("risk_classification", ""),
                "metrics": {
                    "risk_level": site_data.get("risk_level", "Unknown"),
                    "confidence": ml_prediction.get("confidence", 0) if ml_prediction else 0,
                    "dqi": site_data.get("dqi", 0)
                }
            },
            {
                "title": "Key Risk Factors",
                "content": narrative.get("risk_factors", ""),
                "factors": ml_prediction.get("top_risk_factors", []) if ml_prediction else []
            },
            {
                "title": "Data Quality Analysis",
                "content": narrative.get("data_quality", ""),
                "metrics": {
                    "missing_pages": site_data.get("missing_pages", 0),
                    "clean_patient_rate": site_data.get("clean_patient_rate", 0),
                    "query_count": site_data.get("total_queries", 0)
                }
            },
            {
                "title": "Safety Review Status",
                "content": narrative.get("safety_status", ""),
                "metrics": {
                    "sae_count": site_data.get("sae_count", 0),
                    "pending_reviews": site_data.get("pending_sae", 0)
                }
            },
            {
                "title": "Trend Analysis",
                "content": narrative.get("trends", ""),
            }
        ]
        
        return GeneratedReport(
            report_id=report_id,
            report_type=ReportType.SITE_RISK.value,
            title=f"Site Risk Assessment: {site_id}",
            generated_at=datetime.now().isoformat(),
            executive_summary=narrative.get("executive_summary", ""),
            sections=sections,
            recommendations=narrative.get("recommendations", []),
            metrics=site_data,
            status="complete",
            generation_source=self.provider
        )
    
    def generate_cra_performance_report(
        self,
        cra_id: str,
        cra_data: Dict[str, Any],
        activity_logs: List[Dict] = None
    ) -> GeneratedReport:
        """
        Generate CRA performance summary report.
        
        Args:
            cra_id: CRA identifier
            cra_data: CRA metrics and site assignments
            activity_logs: Recent CRA activities
            
        Returns:
            GeneratedReport: Structured CRA performance report
        """
        report_id = f"CRA-{cra_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        context = {
            "cra_id": cra_id,
            "cra_name": cra_data.get("name", cra_id),
            "assigned_sites": cra_data.get("sites", []),
            "site_count": len(cra_data.get("sites", [])),
            "activities": activity_logs or [],
            "metrics": {
                "total_visits": cra_data.get("total_visits", 0),
                "issues_resolved": cra_data.get("issues_resolved", 0),
                "avg_response_time": cra_data.get("avg_response_time", 0),
                "sites_at_risk": cra_data.get("sites_at_risk", 0)
            }
        }
        
        if self.provider == "gemini":
            narrative = self._generate_cra_narrative_llm(context)
        else:
            narrative = self._generate_cra_narrative_template(context)
        
        sections = [
            {
                "title": "Performance Overview",
                "content": narrative.get("overview", "")
            },
            {
                "title": "Site Coverage",
                "content": narrative.get("site_coverage", ""),
                "sites": cra_data.get("sites", [])
            },
            {
                "title": "Activity Analysis",
                "content": narrative.get("activity_analysis", "")
            },
            {
                "title": "Issue Resolution",
                "content": narrative.get("issue_resolution", "")
            }
        ]
        
        return GeneratedReport(
            report_id=report_id,
            report_type=ReportType.CRA_PERFORMANCE.value,
            title=f"CRA Performance Summary: {cra_data.get('name', cra_id)}",
            generated_at=datetime.now().isoformat(),
            executive_summary=narrative.get("executive_summary", ""),
            sections=sections,
            recommendations=narrative.get("recommendations", []),
            metrics=context["metrics"],
            status="complete",
            generation_source=self.provider
        )
    
    def generate_executive_summary(
        self,
        study_id: str,
        study_metrics: Dict[str, Any],
        site_summaries: List[Dict] = None
    ) -> GeneratedReport:
        """
        Generate executive-level study summary.
        
        Args:
            study_id: Study identifier
            study_metrics: Aggregated study-level metrics
            site_summaries: High-level site status summaries
            
        Returns:
            GeneratedReport: Executive dashboard summary
        """
        report_id = f"EXEC-{study_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        context = {
            "study_id": study_id,
            "total_sites": study_metrics.get("total_sites", 0),
            "total_subjects": study_metrics.get("total_subjects", 0),
            "high_risk_sites": study_metrics.get("high_risk_count", 0),
            "medium_risk_sites": study_metrics.get("medium_risk_count", 0),
            "low_risk_sites": study_metrics.get("low_risk_count", 0),
            "overall_dqi": study_metrics.get("avg_dqi", 0),
            "readiness_score": study_metrics.get("readiness_score", 0),
            "pending_saes": study_metrics.get("pending_saes", 0),
            "total_missing_pages": study_metrics.get("total_missing", 0),
            "site_summaries": site_summaries or []
        }
        
        if self.provider == "gemini":
            narrative = self._generate_executive_narrative_llm(context)
        else:
            narrative = self._generate_executive_narrative_template(context)
        
        sections = [
            {
                "title": "Study Health Overview",
                "content": narrative.get("health_overview", ""),
                "metrics": {
                    "dqi": context["overall_dqi"],
                    "readiness": context["readiness_score"]
                }
            },
            {
                "title": "Risk Distribution",
                "content": narrative.get("risk_distribution", ""),
                "breakdown": {
                    "high": context["high_risk_sites"],
                    "medium": context["medium_risk_sites"],
                    "low": context["low_risk_sites"]
                }
            },
            {
                "title": "Safety Status",
                "content": narrative.get("safety_status", "")
            },
            {
                "title": "Data Quality Highlights",
                "content": narrative.get("data_quality", "")
            },
            {
                "title": "Key Actions Required",
                "content": narrative.get("key_actions", "")
            }
        ]
        
        return GeneratedReport(
            report_id=report_id,
            report_type=ReportType.EXECUTIVE_SUMMARY.value,
            title=f"Executive Summary: Study {study_id}",
            generated_at=datetime.now().isoformat(),
            executive_summary=narrative.get("executive_summary", ""),
            sections=sections,
            recommendations=narrative.get("recommendations", []),
            metrics=study_metrics,
            status="complete",
            generation_source=self.provider
        )
    
    def _build_site_context(
        self, 
        site_id: str, 
        site_data: Dict, 
        ml_prediction: Dict = None
    ) -> Dict:
        """Build comprehensive context for site report generation."""
        
        context = {
            "site_id": site_id,
            "risk_level": site_data.get("risk_level", "Unknown"),
            "dqi": site_data.get("dqi", 0),
            "subject_count": site_data.get("subject_count", 0),
            "country": site_data.get("country", "Unknown"),
            
            # Safety metrics
            "sae_count": site_data.get("sae_count", 0),
            "pending_sae": site_data.get("pending_sae", 0),
            
            # Data quality
            "missing_pages": site_data.get("missing_pages", 0),
            "clean_patient_rate": site_data.get("clean_patient_rate", 0),
            "total_queries": site_data.get("total_queries", 0),
            
            # Compliance
            "protocol_deviations": site_data.get("protocol_deviations", 0),
            
            # ML insights
            "ml_confidence": ml_prediction.get("confidence", 0) if ml_prediction else 0,
            "ml_factors": ml_prediction.get("top_risk_factors", []) if ml_prediction else [],
            "dqi_percentile": ml_prediction.get("dqi_percentile", 50) if ml_prediction else 50
        }
        
        return context
    
    def _generate_site_narrative_llm(self, context: Dict) -> Dict[str, Any]:
        """Generate site narrative using Gemini LLM."""
        
        prompt = f"""You are a Clinical Data Quality Expert generating a site risk assessment report.

Site Data:
- Site ID: {context['site_id']}
- Country: {context['country']}
- Risk Level: {context['risk_level']}
- Data Quality Index (DQI): {context['dqi']}/100
- Subject Count: {context['subject_count']}
- SAE Count: {context['sae_count']} (Pending: {context['pending_sae']})
- Missing Pages: {context['missing_pages']}
- Clean Patient Rate: {context['clean_patient_rate']}%
- Protocol Deviations: {context['protocol_deviations']}
- AI Confidence: {context['ml_confidence']:.0%}
- DQI Percentile: {context['dqi_percentile']:.0f}th

Top Risk Factors identified by ML:
{json.dumps(context['ml_factors'][:3], indent=2) if context['ml_factors'] else 'None identified'}

Generate a comprehensive site risk assessment with the following sections (respond in JSON format):
{{
    "executive_summary": "2-3 sentence high-level summary",
    "risk_classification": "Explanation of why this risk level was assigned",
    "risk_factors": "Detailed analysis of the key risk factors",
    "data_quality": "Assessment of data quality issues and patterns",
    "safety_status": "SAE review status and safety concerns",
    "trends": "Any observable trends or patterns",
    "recommendations": ["Action 1", "Action 2", "Action 3"]
}}

Be specific, actionable, and use clinical terminology appropriately."""

        try:
            response = self.model.generate_content(prompt)
            text = response.text
            
            # Parse JSON from response
            # Handle markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            return json.loads(text.strip())
            
        except Exception as e:
            print(f"[ERROR] LLM generation failed: {e}")
            return self._generate_site_narrative_template(context)
    
    def _generate_site_narrative_template(self, context: Dict) -> Dict[str, Any]:
        """Template-based fallback for site narrative."""
        
        risk_level = context['risk_level']
        dqi = context['dqi']
        
        # Dynamic executive summary
        if risk_level == "High":
            exec_summary = f"Site {context['site_id']} requires **immediate attention** with a DQI of {dqi}. Critical issues include elevated safety signals and significant data quality gaps that must be addressed before the next milestone."
        elif risk_level == "Medium":
            exec_summary = f"Site {context['site_id']} shows **moderate risk** with a DQI of {dqi}. While operational, there are areas requiring focused intervention to prevent escalation."
        else:
            exec_summary = f"Site {context['site_id']} is performing within **normal parameters** with a DQI of {dqi}. Continue routine monitoring to maintain current performance levels."
        
        # Risk factors
        factors = []
        if context['pending_sae'] > 0:
            factors.append(f"**{context['pending_sae']} pending SAE reviews** requiring medical monitor attention")
        if context['missing_pages'] > 10:
            factors.append(f"**{context['missing_pages']} missing data pages** contributing to data quality issues")
        if context['protocol_deviations'] > 3:
            factors.append(f"**{context['protocol_deviations']} protocol deviations** indicating compliance concerns")
        
        risk_factors_text = "Key risk factors identified:\n" + "\n".join([f"- {f}" for f in factors]) if factors else "No critical risk factors identified at this time."
        
        # Recommendations
        recommendations = []
        if risk_level == "High":
            recommendations = [
                "Schedule immediate CRA visit for site audit",
                "Escalate pending SAE reviews to Medical Monitor",
                "Implement targeted data entry training",
                "Review protocol compliance with site staff"
            ]
        elif risk_level == "Medium":
            recommendations = [
                "Conduct remote monitoring session",
                "Follow up on missing data entries",
                "Review query aging report"
            ]
        else:
            recommendations = [
                "Continue routine surveillance",
                "Maintain current monitoring cadence"
            ]
        
        return {
            "executive_summary": exec_summary,
            "risk_classification": f"This site has been classified as **{risk_level} Risk** based on a composite Data Quality Index of {dqi}/100, which places it in the {context['dqi_percentile']:.0f}th percentile compared to other sites in the study.",
            "risk_factors": risk_factors_text,
            "data_quality": f"The site has {context['missing_pages']} missing pages across {context['subject_count']} subjects, resulting in a Clean Patient Rate of {context['clean_patient_rate']}%. There are {context['total_queries']} active queries requiring resolution.",
            "safety_status": f"The site has reported {context['sae_count']} Serious Adverse Events, with {context['pending_sae']} pending review. " + ("Immediate medical review is recommended." if context['pending_sae'] > 0 else "All SAEs have been reviewed and closed."),
            "trends": "Trend analysis requires historical data. Based on current snapshot, the site shows consistent patterns with identified risk factors.",
            "recommendations": recommendations
        }
    
    def _generate_cra_narrative_llm(self, context: Dict) -> Dict[str, Any]:
        """Generate CRA performance narrative using LLM."""
        
        prompt = f"""You are a Clinical Operations Manager evaluating CRA performance.

CRA Data:
- CRA: {context['cra_name']}
- Assigned Sites: {context['site_count']}
- Total Visits: {context['metrics']['total_visits']}
- Issues Resolved: {context['metrics']['issues_resolved']}
- Avg Response Time: {context['metrics']['avg_response_time']} hours
- Sites at Risk: {context['metrics']['sites_at_risk']}

Recent Activities:
{json.dumps(context['activities'][:5], indent=2) if context['activities'] else 'No recent activities logged'}

Generate a CRA performance assessment (respond in JSON format):
{{
    "executive_summary": "2-3 sentence performance summary",
    "overview": "Overall performance assessment",
    "site_coverage": "Analysis of site management and coverage",
    "activity_analysis": "Review of recent activities and patterns",
    "issue_resolution": "Assessment of issue handling",
    "recommendations": ["Recommendation 1", "Recommendation 2"]
}}"""

        try:
            response = self.model.generate_content(prompt)
            text = response.text
            
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            return json.loads(text.strip())
            
        except Exception as e:
            print(f"[ERROR] CRA LLM generation failed: {e}")
            return self._generate_cra_narrative_template(context)
    
    def _generate_cra_narrative_template(self, context: Dict) -> Dict[str, Any]:
        """Template fallback for CRA narrative."""
        
        return {
            "executive_summary": f"{context['cra_name']} is managing {context['site_count']} sites with {context['metrics']['sites_at_risk']} currently flagged as at-risk. Response metrics indicate {'prompt attention to site needs' if context['metrics']['avg_response_time'] < 24 else 'opportunity for improved responsiveness'}.",
            "overview": f"CRA {context['cra_name']} has conducted {context['metrics']['total_visits']} visits and resolved {context['metrics']['issues_resolved']} issues in the review period.",
            "site_coverage": f"Currently assigned to {context['site_count']} sites. Coverage appears {'adequate' if context['site_count'] <= 10 else 'heavy - consider load balancing'}.",
            "activity_analysis": f"Recent activity shows engagement with assigned sites. Average response time of {context['metrics']['avg_response_time']} hours is {'within SLA' if context['metrics']['avg_response_time'] < 48 else 'outside target SLA'}.",
            "issue_resolution": f"Resolved {context['metrics']['issues_resolved']} issues. Sites at risk: {context['metrics']['sites_at_risk']}.",
            "recommendations": [
                "Prioritize at-risk sites for next visit cycle",
                "Document all site interactions in activity log",
                "Coordinate with Medical Monitor on pending SAEs"
            ]
        }
    
    def _generate_executive_narrative_llm(self, context: Dict) -> Dict[str, Any]:
        """Generate executive summary using LLM."""
        
        prompt = f"""You are a Clinical Operations Director preparing an executive summary for leadership.

Study Metrics:
- Study ID: {context['study_id']}
- Total Sites: {context['total_sites']}
- Total Subjects: {context['total_subjects']}
- Risk Distribution: {context['high_risk_sites']} High, {context['medium_risk_sites']} Medium, {context['low_risk_sites']} Low
- Overall DQI: {context['overall_dqi']}/100
- Readiness Score: {context['readiness_score']}%
- Pending SAEs: {context['pending_saes']}
- Missing Pages: {context['total_missing_pages']}

Generate an executive summary for leadership (respond in JSON format):
{{
    "executive_summary": "3-4 sentence high-level summary for C-suite",
    "health_overview": "Study health status explanation",
    "risk_distribution": "Analysis of risk across sites",
    "safety_status": "Safety signal summary",
    "data_quality": "Data quality highlights",
    "key_actions": "Priority actions for leadership attention",
    "recommendations": ["Strategic recommendation 1", "Strategic recommendation 2", "Strategic recommendation 3"]
}}

Use executive language - concise, action-oriented, and focused on business impact."""

        try:
            response = self.model.generate_content(prompt)
            text = response.text
            
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            return json.loads(text.strip())
            
        except Exception as e:
            print(f"[ERROR] Executive LLM generation failed: {e}")
            return self._generate_executive_narrative_template(context)
    
    def _generate_executive_narrative_template(self, context: Dict) -> Dict[str, Any]:
        """Template fallback for executive narrative."""
        
        high_risk_pct = (context['high_risk_sites'] / max(1, context['total_sites'])) * 100
        
        # Executive summary based on overall health
        if context['overall_dqi'] >= 80 and high_risk_pct < 10:
            status = "on track"
            exec_summary = f"Study {context['study_id']} is performing well with an overall DQI of {context['overall_dqi']}. {context['high_risk_sites']} of {context['total_sites']} sites require attention. Dataset readiness stands at {context['readiness_score']:.1f}%, positioning the study well for upcoming milestones."
        elif context['overall_dqi'] >= 60:
            status = "requires attention"
            exec_summary = f"Study {context['study_id']} shows moderate risk indicators with a DQI of {context['overall_dqi']}. {context['high_risk_sites']} sites are flagged high-risk, requiring focused intervention. Current readiness is {context['readiness_score']:.1f}%."
        else:
            status = "at risk"
            exec_summary = f"**Critical**: Study {context['study_id']} shows significant concerns with a DQI of {context['overall_dqi']}. {context['high_risk_sites']} high-risk sites and {context['pending_saes']} pending SAEs require immediate escalation. Readiness score of {context['readiness_score']:.1f}% may impact timeline."
        
        return {
            "executive_summary": exec_summary,
            "health_overview": f"Study health is currently **{status}** with an aggregate Data Quality Index of {context['overall_dqi']}/100 across {context['total_sites']} active sites and {context['total_subjects']} enrolled subjects.",
            "risk_distribution": f"Risk distribution: **{context['high_risk_sites']}** High ({high_risk_pct:.0f}%), **{context['medium_risk_sites']}** Medium, **{context['low_risk_sites']}** Low. " + ("High-risk concentration requires immediate intervention." if high_risk_pct > 20 else "Distribution is within acceptable parameters."),
            "safety_status": f"There are **{context['pending_saes']} pending SAE reviews** across the study. " + ("Immediate escalation to Medical Monitor recommended." if context['pending_saes'] > 5 else "Safety review cadence is adequate."),
            "data_quality": f"**{context['total_missing_pages']} missing pages** identified globally. Clean patient rate impacts dataset integrity. Focus on backlog reduction is recommended.",
            "key_actions": "Priority actions: 1) Address high-risk sites through targeted monitoring, 2) Clear pending SAE backlog, 3) Implement data entry quality initiatives at underperforming sites.",
            "recommendations": [
                "Allocate additional CRA resources to high-risk sites",
                "Establish weekly safety review calls with Medical Monitor",
                "Implement automated missing data alerts",
                "Consider site-specific training interventions"
            ]
        }


# Singleton instance for service usage
_generator_instance: Optional[LLMReportGenerator] = None


def get_report_generator() -> LLMReportGenerator:
    """Get singleton report generator instance."""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = LLMReportGenerator()
    return _generator_instance
