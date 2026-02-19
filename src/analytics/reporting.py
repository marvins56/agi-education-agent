"""
Reporting Module

Generates comprehensive reports for different stakeholders (students, parents, teachers, administrators).
Supports multiple export formats and languages.
"""

import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import io
from pathlib import Path

from .student_analytics import StudentAnalytics, LearningStyle
from .class_analytics import ClassAnalytics, RiskLevel, AtRiskStudent


class ReportType(Enum):
    """Types of reports available"""
    STUDENT_PROGRESS = "student_progress"
    PARENT_SUMMARY = "parent_summary"
    TEACHER_CLASS = "teacher_class"
    ADMINISTRATOR = "administrator"


class ExportFormat(Enum):
    """Export formats supported"""
    JSON = "json"
    CSV = "csv"
    PDF_DATA = "pdf_data"  # Structured data ready for PDF generation


class Language(Enum):
    """Supported languages"""
    ENGLISH = "en"
    SWAHILI = "sw"
    LUGANDA = "lg"


@dataclass
class ReportTemplate:
    """Template for report generation"""
    report_type: ReportType
    language: Language
    title: str
    sections: List[str]
    translations: Dict[str, str]


@dataclass
class ScheduledReport:
    """Configuration for scheduled reports"""
    report_id: str
    report_type: ReportType
    target_ids: List[str]  # Student IDs, Class IDs, etc.
    schedule: str  # "weekly", "monthly", "daily"
    format: ExportFormat
    language: Language
    recipients: List[str]  # Email addresses or notification targets
    next_run: datetime
    active: bool = True


class ReportGenerator:
    """
    Generates comprehensive reports for various stakeholders in multiple formats and languages.
    """
    
    def __init__(self):
        self.templates: Dict[Tuple[ReportType, Language], ReportTemplate] = {}
        self.scheduled_reports: List[ScheduledReport] = []
        self._load_templates()
    
    def _load_templates(self):
        """Load report templates with translations"""
        
        # English Templates
        self.templates[(ReportType.STUDENT_PROGRESS, Language.ENGLISH)] = ReportTemplate(
            report_type=ReportType.STUDENT_PROGRESS,
            language=Language.ENGLISH,
            title="Student Progress Report",
            sections=["summary", "performance", "learning_style", "recommendations"],
            translations={
                "summary": "Summary",
                "performance": "Performance Analysis",
                "learning_style": "Learning Style",
                "recommendations": "Recommendations",
                "excellent": "Excellent",
                "good": "Good",
                "needs_improvement": "Needs Improvement",
                "math": "Mathematics",
                "science": "Science",
                "english": "English",
                "social_studies": "Social Studies",
                "visual": "Visual Learner",
                "auditory": "Auditory Learner",
                "kinesthetic": "Hands-on Learner",
                "reading_writing": "Reading/Writing Learner",
                "mixed": "Mixed Learning Style"
            }
        )
        
        self.templates[(ReportType.PARENT_SUMMARY, Language.ENGLISH)] = ReportTemplate(
            report_type=ReportType.PARENT_SUMMARY,
            language=Language.ENGLISH,
            title="Parent Progress Summary",
            sections=["overview", "strengths", "areas_for_growth", "home_support"],
            translations={
                "overview": "Learning Overview",
                "strengths": "Your Child's Strengths",
                "areas_for_growth": "Areas for Growth",
                "home_support": "How You Can Help at Home",
                "engaged": "actively engaged",
                "progressing": "making good progress",
                "struggling": "needs extra support"
            }
        )
        
        # Swahili Templates
        self.templates[(ReportType.STUDENT_PROGRESS, Language.SWAHILI)] = ReportTemplate(
            report_type=ReportType.STUDENT_PROGRESS,
            language=Language.SWAHILI,
            title="Ripoti ya Maendeleo ya Mwanafunzi",
            sections=["muhtasari", "utendaji", "mtindo_wa_kujifunza", "mapendekezo"],
            translations={
                "summary": "Muhtasari",
                "performance": "Uchambuzi wa Utendaji",
                "learning_style": "Mtindo wa Kujifunza",
                "recommendations": "Mapendekezo",
                "excellent": "Bora Sana",
                "good": "Vizuri",
                "needs_improvement": "Inahitaji Uboreshaji",
                "math": "Hisabati",
                "science": "Sayansi",
                "english": "Kiingereza",
                "social_studies": "Utaalamu wa Kijamii",
                "visual": "Mjifunzi wa Kuona",
                "auditory": "Mjifunzi wa Kusikia",
                "kinesthetic": "Mjifunzi wa Vitendo",
                "reading_writing": "Mjifunzi wa Kusoma/Kuandika",
                "mixed": "Mtindo wa Kujifunza Mchanganyiko"
            }
        )
        
        self.templates[(ReportType.PARENT_SUMMARY, Language.SWAHILI)] = ReportTemplate(
            report_type=ReportType.PARENT_SUMMARY,
            language=Language.SWAHILI,
            title="Muhtasari wa Maendeleo kwa Wazazi",
            sections=["muongozo", "nguvu", "maeneo_ya_ukuaji", "msaada_nyumbani"],
            translations={
                "overview": "Muongozo wa Kujifunza",
                "strengths": "Nguvu za Mtoto Wako",
                "areas_for_growth": "Maeneo ya Ukuaji",
                "home_support": "Jinsi Unavyoweza Kusaidia Nyumbani",
                "engaged": "ameshiriki kwa bidii",
                "progressing": "anaendelea vizuri",
                "struggling": "anahitaji msaada zaidi"
            }
        )
        
        # Luganda Templates  
        self.templates[(ReportType.PARENT_SUMMARY, Language.LUGANDA)] = ReportTemplate(
            report_type=ReportType.PARENT_SUMMARY,
            language=Language.LUGANDA,
            title="Lipooti y'Enkulaakulana eri Bazadde",
            sections=["okwetegereza", "maanyi", "ebifo_by'okukula", "obuyambi_ewaka"],
            translations={
                "overview": "Okwetegereza Okuyiga",
                "strengths": "Amaanyi g'Omwana wo",
                "areas_for_growth": "Ebifo by'Okukula",
                "home_support": "Engeri gy'Oyinza Okuyambako ewaka",
                "engaged": "yeenyigidde mu kusoma",
                "progressing": "agenda maaso bulungi",
                "struggling": "yeetaaga obuyambi obw'enjawulo"
            }
        )
    
    def generate_student_progress_report(
        self, 
        student_analytics: StudentAnalytics, 
        language: Language = Language.ENGLISH,
        format: ExportFormat = ExportFormat.JSON
    ) -> Dict[str, Any]:
        """
        Generate a detailed student progress report.
        
        Args:
            student_analytics: Student's analytics data
            language: Report language
            format: Export format
            
        Returns:
            Structured report data
        """
        template = self.templates.get((ReportType.STUDENT_PROGRESS, language))
        if not template:
            template = self.templates[(ReportType.STUDENT_PROGRESS, Language.ENGLISH)]
        
        # Get comprehensive student data
        report_data = student_analytics.get_comprehensive_report()
        
        # Build structured report
        report = {
            "report_info": {
                "type": "student_progress",
                "student_id": student_analytics.student_id,
                "generated_at": datetime.now().isoformat(),
                "language": language.value,
                "title": template.title
            },
            "summary": self._build_student_summary(report_data, template),
            "performance": self._build_performance_section(report_data, template),
            "learning_style": self._build_learning_style_section(report_data, template),
            "recommendations": self._build_student_recommendations(report_data, template),
            "metrics": {
                "engagement_score": report_data["engagement_score"]["overall"],
                "learning_velocity": report_data["learning_velocity"],
                "retention_rate": report_data["retention_rate"],
                "optimal_study_time": report_data["optimal_study_time"],
                "total_sessions": report_data["total_sessions"]
            }
        }
        
        return self._format_report(report, format)
    
    def generate_parent_summary_report(
        self, 
        student_analytics: StudentAnalytics, 
        language: Language = Language.ENGLISH,
        format: ExportFormat = ExportFormat.JSON
    ) -> Dict[str, Any]:
        """
        Generate a parent-friendly summary report with simple, visual descriptions.
        
        Args:
            student_analytics: Student's analytics data
            language: Report language
            format: Export format
            
        Returns:
            Parent-friendly report data
        """
        template = self.templates.get((ReportType.PARENT_SUMMARY, language))
        if not template:
            template = self.templates[(ReportType.PARENT_SUMMARY, Language.ENGLISH)]
        
        report_data = student_analytics.get_comprehensive_report()
        
        report = {
            "report_info": {
                "type": "parent_summary",
                "student_id": student_analytics.student_id,
                "generated_at": datetime.now().isoformat(),
                "language": language.value,
                "title": template.title
            },
            "overview": self._build_parent_overview(report_data, template),
            "strengths": self._identify_student_strengths(report_data, template),
            "areas_for_growth": self._identify_growth_areas(report_data, template),
            "home_support": self._generate_home_support_suggestions(report_data, template),
            "visual_summary": self._create_visual_summary_data(report_data)
        }
        
        return self._format_report(report, format)
    
    def generate_teacher_class_report(
        self, 
        class_analytics: ClassAnalytics, 
        language: Language = Language.ENGLISH,
        format: ExportFormat = ExportFormat.JSON
    ) -> Dict[str, Any]:
        """
        Generate a detailed, actionable report for teachers.
        
        Args:
            class_analytics: Class analytics data
            language: Report language  
            format: Export format
            
        Returns:
            Teacher-focused report with actionable insights
        """
        class_report = class_analytics.get_comprehensive_class_report()
        
        report = {
            "report_info": {
                "type": "teacher_class",
                "class_id": class_analytics.class_id,
                "teacher_id": class_analytics.teacher_id,
                "generated_at": datetime.now().isoformat(),
                "language": language.value,
                "title": "Class Performance Report" if language == Language.ENGLISH else "Ripoti ya Utendaji wa Darasa"
            },
            "class_overview": {
                "total_students": class_report["total_students"],
                "class_summary": class_report["class_summary"],
                "overall_trends": self._analyze_class_trends(class_report)
            },
            "performance_insights": {
                "struggling_topics": self._identify_struggling_topics(class_report["performance_heatmap"]),
                "high_performing_areas": self._identify_high_performing_areas(class_report["performance_heatmap"]),
                "comparative_performance": class_report["comparative_analytics"]
            },
            "student_insights": {
                "at_risk_students": class_report["at_risk_students"],
                "engagement_distribution": self._analyze_engagement_distribution(class_analytics),
                "learning_pace_analysis": self._analyze_learning_pace(class_analytics)
            },
            "teaching_effectiveness": class_report["teacher_effectiveness"],
            "resource_recommendations": self._generate_resource_recommendations(class_report),
            "action_items": self._generate_teacher_action_items(class_report, language)
        }
        
        return self._format_report(report, format)
    
    def generate_administrator_report(
        self, 
        class_analytics_list: List[ClassAnalytics], 
        language: Language = Language.ENGLISH,
        format: ExportFormat = ExportFormat.JSON
    ) -> Dict[str, Any]:
        """
        Generate aggregate metrics report for school administrators.
        
        Args:
            class_analytics_list: List of class analytics
            language: Report language
            format: Export format
            
        Returns:
            Administrator-focused aggregate report
        """
        # Aggregate data from all classes
        total_students = sum(len(ca.student_analytics) for ca in class_analytics_list)
        total_teachers = len(class_analytics_list)
        
        report = {
            "report_info": {
                "type": "administrator",
                "generated_at": datetime.now().isoformat(),
                "language": language.value,
                "title": "School Performance Overview" if language == Language.ENGLISH else "Muhtasari wa Utendaji wa Shule"
            },
            "school_overview": {
                "total_students": total_students,
                "total_teachers": total_teachers,
                "total_classes": len(class_analytics_list),
                "report_period": self._get_report_period()
            },
            "aggregate_performance": self._calculate_aggregate_performance(class_analytics_list),
            "teacher_effectiveness_summary": self._aggregate_teacher_effectiveness(class_analytics_list),
            "at_risk_analysis": self._aggregate_at_risk_analysis(class_analytics_list),
            "resource_utilization": self._aggregate_resource_utilization(class_analytics_list),
            "trends_and_insights": self._generate_school_trends(class_analytics_list),
            "recommendations": self._generate_admin_recommendations(class_analytics_list, language)
        }
        
        return self._format_report(report, format)
    
    def _build_student_summary(self, report_data: Dict, template: ReportTemplate) -> Dict:
        """Build student summary section"""
        engagement = report_data["engagement_score"]["overall"]
        
        if engagement >= 0.8:
            engagement_desc = template.translations.get("excellent", "Excellent")
        elif engagement >= 0.6:
            engagement_desc = template.translations.get("good", "Good")
        else:
            engagement_desc = template.translations.get("needs_improvement", "Needs Improvement")
        
        return {
            "engagement_level": engagement_desc,
            "engagement_score": engagement,
            "active_subjects": list(report_data["learning_velocity"].keys()),
            "total_study_sessions": report_data["total_sessions"],
            "learning_pace": "Steady" if report_data["total_sessions"] > 10 else "Getting Started"
        }
    
    def _build_performance_section(self, report_data: Dict, template: ReportTemplate) -> Dict:
        """Build performance analysis section"""
        performance = {}
        
        for subject, retention in report_data["retention_rate"].items():
            translated_subject = template.translations.get(subject.lower(), subject)
            
            if retention >= 0.8:
                level = template.translations.get("excellent", "Excellent")
            elif retention >= 0.6:
                level = template.translations.get("good", "Good")  
            else:
                level = template.translations.get("needs_improvement", "Needs Improvement")
            
            performance[translated_subject] = {
                "retention_rate": round(retention, 2),
                "performance_level": level,
                "learning_velocity": report_data["learning_velocity"].get(subject, 0)
            }
        
        return performance
    
    def _build_learning_style_section(self, report_data: Dict, template: ReportTemplate) -> Dict:
        """Build learning style section"""
        style_info = report_data["learning_style"]
        style_key = style_info["style"].value if hasattr(style_info["style"], 'value') else str(style_info["style"])
        
        return {
            "primary_style": template.translations.get(style_key, style_key.title()),
            "confidence": style_info["confidence"],
            "style_breakdown": {
                template.translations.get(k, k.title()): v 
                for k, v in style_info["scores"].items()
            },
            "recommendation": self._get_learning_style_recommendation(style_key, template.language)
        }
    
    def _build_student_recommendations(self, report_data: Dict, template: ReportTemplate) -> List[str]:
        """Generate student-specific recommendations"""
        recommendations = []
        
        # Based on engagement
        engagement = report_data["engagement_score"]["overall"]
        if engagement < 0.5:
            if template.language == Language.ENGLISH:
                recommendations.append("Try shorter, more frequent study sessions")
            elif template.language == Language.SWAHILI:
                recommendations.append("Jaribu vipindi vya kusoma vifupi na mara kwa mara")
        
        # Based on optimal study time
        optimal_time = report_data["optimal_study_time"]
        if optimal_time.get("optimal_period") != "insufficient_data":
            if template.language == Language.ENGLISH:
                recommendations.append(f"Schedule study sessions during {optimal_time['optimal_period']} for best results")
            elif template.language == Language.SWAHILI:
                recommendations.append(f"Panga vipindi vya kusoma wakati wa {optimal_time['optimal_period']} kwa matokeo bora")
        
        # Based on learning style
        style = report_data["learning_style"]["style"]
        if hasattr(style, 'value'):
            style_value = style.value
        else:
            style_value = str(style)
            
        style_rec = self._get_learning_style_recommendation(style_value, template.language)
        if style_rec:
            recommendations.append(style_rec)
        
        return recommendations
    
    def _build_parent_overview(self, report_data: Dict, template: ReportTemplate) -> Dict:
        """Build parent-friendly overview"""
        engagement = report_data["engagement_score"]["overall"]
        
        if engagement >= 0.7:
            status = template.translations.get("engaged", "actively engaged")
        elif engagement >= 0.5:
            status = template.translations.get("progressing", "making good progress")
        else:
            status = template.translations.get("struggling", "needs extra support")
        
        return {
            "learning_status": status,
            "favorite_subjects": self._identify_favorite_subjects(report_data),
            "study_habits": self._describe_study_habits(report_data, template.language),
            "recent_achievements": self._identify_recent_achievements(report_data)
        }
    
    def _identify_student_strengths(self, report_data: Dict, template: ReportTemplate) -> List[str]:
        """Identify student's key strengths"""
        strengths = []
        
        # High retention subjects
        for subject, retention in report_data["retention_rate"].items():
            if retention >= 0.8:
                subject_name = template.translations.get(subject.lower(), subject)
                strengths.append(f"Strong understanding in {subject_name}")
        
        # High engagement
        if report_data["engagement_score"]["overall"] >= 0.7:
            strengths.append("Consistent study habits" if template.language == Language.ENGLISH 
                           else "Mienendo ya kudumu ya kusoma")
        
        # Good learning velocity
        fast_subjects = [s for s, v in report_data["learning_velocity"].items() if v >= 1.0]
        if fast_subjects:
            strengths.append("Quick learning pace" if template.language == Language.ENGLISH 
                           else "Kasi nzuri ya kujifunza")
        
        return strengths[:5]  # Top 5 strengths
    
    def _identify_growth_areas(self, report_data: Dict, template: ReportTemplate) -> List[str]:
        """Identify areas where student can grow"""
        growth_areas = []
        
        # Low retention subjects
        for subject, retention in report_data["retention_rate"].items():
            if retention < 0.6:
                subject_name = template.translations.get(subject.lower(), subject)
                growth_areas.append(f"Needs practice in {subject_name}")
        
        # Low engagement components
        engagement = report_data["engagement_score"]
        if engagement["frequency"] < 0.5:
            growth_areas.append("More regular study schedule" if template.language == Language.ENGLISH
                              else "Ratiba ya mazoezi ya kawaida zaidi")
        
        if engagement["completion"] < 0.7:
            growth_areas.append("Completing learning activities" if template.language == Language.ENGLISH
                              else "Kukamilisha shughuli za kujifunza")
        
        return growth_areas[:4]  # Top 4 growth areas
    
    def _generate_home_support_suggestions(self, report_data: Dict, template: ReportTemplate) -> List[str]:
        """Generate suggestions for parents to support learning at home"""
        suggestions = []
        
        optimal_time = report_data["optimal_study_time"]
        if optimal_time.get("optimal_period") != "insufficient_data":
            period = optimal_time["optimal_period"]
            if template.language == Language.ENGLISH:
                suggestions.append(f"Create a quiet study space for {period} sessions")
            elif template.language == Language.SWAHILI:
                suggestions.append(f"Tengeneza mazingira ya kimya kwa vipindi vya {period}")
        
        # Learning style suggestions
        style = report_data["learning_style"]["style"]
        if hasattr(style, 'value'):
            style_value = style.value
        else:
            style_value = str(style)
            
        if style_value == "visual":
            if template.language == Language.ENGLISH:
                suggestions.append("Use charts, diagrams, and colorful materials")
            elif template.language == Language.SWAHILI:
                suggestions.append("Tumia chati, mchoro, na vifaa vya rangi mbalimbali")
        elif style_value == "auditory":
            if template.language == Language.ENGLISH:
                suggestions.append("Read aloud together and use educational songs")
            elif template.language == Language.SWAHILI:
                suggestions.append("Someni kwa sauti pamoja na kutumia nyimbo za kielimu")
        
        # General encouragement
        if template.language == Language.ENGLISH:
            suggestions.append("Celebrate small victories and progress")
        elif template.language == Language.SWAHILI:
            suggestions.append("Sherehe ushindi mdogo na maendeleo")
        elif template.language == Language.LUGANDA:
            suggestions.append("Jaguza obuwanguzi obumotono n'enkulaakulana")
        
        return suggestions
    
    def _create_visual_summary_data(self, report_data: Dict) -> Dict:
        """Create data for visual charts and graphs"""
        return {
            "engagement_chart": {
                "overall": report_data["engagement_score"]["overall"],
                "frequency": report_data["engagement_score"]["frequency"],
                "duration": report_data["engagement_score"]["duration"],
                "completion": report_data["engagement_score"]["completion"]
            },
            "subject_performance": report_data["retention_rate"],
            "learning_velocity": report_data["learning_velocity"],
            "study_time_preference": report_data["optimal_study_time"].get("optimal_period", "varied")
        }
    
    def _format_report(self, report: Dict, format: ExportFormat) -> Dict[str, Any]:
        """Format report according to specified format"""
        if format == ExportFormat.JSON:
            return report
        elif format == ExportFormat.CSV:
            return self._convert_to_csv_data(report)
        elif format == ExportFormat.PDF_DATA:
            return self._prepare_pdf_data(report)
        else:
            return report
    
    def _convert_to_csv_data(self, report: Dict) -> Dict[str, str]:
        """Convert report to CSV-friendly format"""
        csv_buffer = io.StringIO()
        
        # Flatten the report structure for CSV
        flattened = self._flatten_dict(report)
        
        writer = csv.DictWriter(csv_buffer, fieldnames=flattened.keys())
        writer.writeheader()
        writer.writerow(flattened)
        
        return {
            "format": "csv",
            "data": csv_buffer.getvalue(),
            "filename": f"{report.get('report_info', {}).get('type', 'report')}_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    
    def _prepare_pdf_data(self, report: Dict) -> Dict:
        """Prepare data optimized for PDF generation"""
        return {
            "format": "pdf_data",
            "title": report.get("report_info", {}).get("title", "Report"),
            "sections": report,
            "charts_data": report.get("visual_summary", {}),
            "metadata": report.get("report_info", {})
        }
    
    def _flatten_dict(self, d: Dict, parent_key: str = "", sep: str = "_") -> Dict:
        """Flatten nested dictionary for CSV export"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep).items())
            elif isinstance(v, list):
                items.append((new_key, "; ".join(str(item) for item in v)))
            else:
                items.append((new_key, str(v)))
        return dict(items)
    
    def _get_learning_style_recommendation(self, style: str, language: Language) -> str:
        """Get learning style specific recommendations"""
        recommendations = {
            Language.ENGLISH: {
                "visual": "Use diagrams, charts, and visual aids while studying",
                "auditory": "Try explaining concepts aloud or listening to educational content",
                "kinesthetic": "Incorporate hands-on activities and movement in learning",
                "reading_writing": "Take detailed notes and create written summaries",
                "mixed": "Combine different learning approaches for best results"
            },
            Language.SWAHILI: {
                "visual": "Tumia michoro, chati, na vifaa vya kuona wakati wa kusoma",
                "auditory": "Jaribu kueleza dhana kwa sauti au kusikiliza maudhui ya kielimu",
                "kinesthetic": "Jumuisha shughuli za vitendo na harakati katika kujifunza",
                "reading_writing": "Chukua maelezo ya kina na uunde muhtasari wa maandishi",
                "mixed": "Changanya mbinu mbalimbali za kujifunza kwa matokeo bora"
            }
        }
        
        return recommendations.get(language, recommendations[Language.ENGLISH]).get(style, "")
    
    def add_scheduled_report(self, scheduled_report: ScheduledReport):
        """Add a scheduled report configuration"""
        self.scheduled_reports.append(scheduled_report)
    
    def get_due_reports(self) -> List[ScheduledReport]:
        """Get reports that are due to be generated"""
        now = datetime.now()
        return [report for report in self.scheduled_reports 
                if report.active and report.next_run <= now]
    
    def update_next_run(self, report_id: str):
        """Update the next run time for a scheduled report"""
        for report in self.scheduled_reports:
            if report.report_id == report_id:
                if report.schedule == "daily":
                    report.next_run = datetime.now() + timedelta(days=1)
                elif report.schedule == "weekly":
                    report.next_run = datetime.now() + timedelta(weeks=1)
                elif report.schedule == "monthly":
                    report.next_run = datetime.now() + timedelta(days=30)
                break
    
    # Helper methods for class and admin reports
    def _analyze_class_trends(self, class_report: Dict) -> Dict:
        """Analyze overall class trends"""
        return {
            "performance_trend": "stable",  # Would be calculated from historical data
            "engagement_trend": "improving",  # Placeholder
            "at_risk_trend": "decreasing"  # Placeholder
        }
    
    def _identify_struggling_topics(self, heatmap: Dict) -> List[Dict]:
        """Identify topics where students are struggling most"""
        struggling = []
        for subject, topics in heatmap.items():
            for topic, metric in topics.items():
                if metric.avg_score < 65 or metric.struggle_count > metric.student_count * 0.5:
                    struggling.append({
                        "subject": subject,
                        "topic": topic,
                        "avg_score": metric.avg_score,
                        "students_struggling": metric.struggle_count,
                        "total_students": metric.student_count
                    })
        
        return sorted(struggling, key=lambda x: x["avg_score"])[:5]
    
    def _identify_high_performing_areas(self, heatmap: Dict) -> List[Dict]:
        """Identify high-performing topics"""
        high_performing = []
        for subject, topics in heatmap.items():
            for topic, metric in topics.items():
                if metric.avg_score >= 85 and metric.student_count >= 3:
                    high_performing.append({
                        "subject": subject,
                        "topic": topic,
                        "avg_score": metric.avg_score,
                        "student_count": metric.student_count
                    })
        
        return sorted(high_performing, key=lambda x: x["avg_score"], reverse=True)[:5]
    
    def _analyze_engagement_distribution(self, class_analytics: ClassAnalytics) -> Dict:
        """Analyze engagement distribution across the class"""
        engagement_scores = []
        for analytics in class_analytics.student_analytics.values():
            engagement = analytics.calculate_engagement_score()
            engagement_scores.append(engagement['overall'])
        
        if engagement_scores:
            return {
                "average": round(sum(engagement_scores) / len(engagement_scores), 3),
                "high_engagement": sum(1 for score in engagement_scores if score >= 0.7),
                "medium_engagement": sum(1 for score in engagement_scores if 0.4 <= score < 0.7),
                "low_engagement": sum(1 for score in engagement_scores if score < 0.4)
            }
        return {"average": 0, "high_engagement": 0, "medium_engagement": 0, "low_engagement": 0}
    
    def _analyze_learning_pace(self, class_analytics: ClassAnalytics) -> Dict:
        """Analyze learning pace across the class"""
        pace_data = []
        for analytics in class_analytics.student_analytics.values():
            velocity = analytics.get_learning_velocity()
            if velocity:
                avg_velocity = sum(velocity.values()) / len(velocity)
                pace_data.append(avg_velocity)
        
        if pace_data:
            return {
                "average_velocity": round(sum(pace_data) / len(pace_data), 2),
                "fast_learners": sum(1 for pace in pace_data if pace >= 1.5),
                "steady_learners": sum(1 for pace in pace_data if 0.5 <= pace < 1.5),
                "slow_learners": sum(1 for pace in pace_data if pace < 0.5)
            }
        return {"average_velocity": 0, "fast_learners": 0, "steady_learners": 0, "slow_learners": 0}
    
    def _generate_resource_recommendations(self, class_report: Dict) -> List[str]:
        """Generate resource recommendations based on class performance"""
        recommendations = []
        
        # Based on struggling topics
        if "performance_insights" in class_report:
            struggling = class_report["performance_insights"].get("struggling_topics", [])
            for topic_info in struggling[:3]:  # Top 3 struggling areas
                recommendations.append(f"Additional practice materials needed for {topic_info['subject']} - {topic_info['topic']}")
        
        return recommendations
    
    def _generate_teacher_action_items(self, class_report: Dict, language: Language) -> List[str]:
        """Generate specific action items for teachers"""
        actions = []
        
        at_risk_count = len(class_report.get("at_risk_students", []))
        if at_risk_count > 0:
            if language == Language.ENGLISH:
                actions.append(f"Schedule individual meetings with {at_risk_count} at-risk students")
            else:
                actions.append(f"Panga mikutano ya kibinafsi na wanafunzi {at_risk_count} walio hatarini")
        
        return actions
    
    def _get_report_period(self) -> Dict:
        """Get the current report period"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # Last 30 days
        
        return {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "period_type": "monthly"
        }
    
    def _calculate_aggregate_performance(self, class_analytics_list: List[ClassAnalytics]) -> Dict:
        """Calculate aggregate performance across all classes"""
        all_scores = []
        all_engagement = []
        
        for class_analytics in class_analytics_list:
            for analytics in class_analytics.student_analytics.values():
                # Collect scores
                for session in analytics.sessions:
                    if session.score is not None:
                        all_scores.append(session.score)
                
                # Collect engagement
                engagement = analytics.calculate_engagement_score()
                all_engagement.append(engagement['overall'])
        
        if all_scores and all_engagement:
            return {
                "average_score": round(sum(all_scores) / len(all_scores), 2),
                "average_engagement": round(sum(all_engagement) / len(all_engagement), 3),
                "total_sessions": len(all_scores),
                "score_distribution": {
                    "excellent": sum(1 for score in all_scores if score >= 90),
                    "good": sum(1 for score in all_scores if 80 <= score < 90),
                    "fair": sum(1 for score in all_scores if 70 <= score < 80),
                    "needs_improvement": sum(1 for score in all_scores if score < 70)
                }
            }
        
        return {"error": "Insufficient data for aggregate analysis"}
    
    def _aggregate_teacher_effectiveness(self, class_analytics_list: List[ClassAnalytics]) -> Dict:
        """Aggregate teacher effectiveness across all classes"""
        effectiveness_scores = []
        
        for class_analytics in class_analytics_list:
            effectiveness = class_analytics.analyze_teacher_effectiveness()
            if 'overall_score' in effectiveness:
                effectiveness_scores.append(effectiveness['overall_score'])
        
        if effectiveness_scores:
            return {
                "average_effectiveness": round(sum(effectiveness_scores) / len(effectiveness_scores), 3),
                "high_performing_teachers": sum(1 for score in effectiveness_scores if score >= 0.8),
                "teachers_needing_support": sum(1 for score in effectiveness_scores if score < 0.6)
            }
        
        return {"average_effectiveness": 0, "high_performing_teachers": 0, "teachers_needing_support": 0}
    
    def _aggregate_at_risk_analysis(self, class_analytics_list: List[ClassAnalytics]) -> Dict:
        """Aggregate at-risk student analysis"""
        total_students = 0
        total_at_risk = 0
        risk_levels = {"critical": 0, "high": 0, "medium": 0}
        
        for class_analytics in class_analytics_list:
            total_students += len(class_analytics.student_analytics)
            at_risk_students = class_analytics.identify_at_risk_students()
            total_at_risk += len(at_risk_students)
            
            for student in at_risk_students:
                risk_levels[student.risk_level.value] += 1
        
        if total_students > 0:
            return {
                "total_students": total_students,
                "total_at_risk": total_at_risk,
                "at_risk_percentage": round((total_at_risk / total_students) * 100, 1),
                "risk_breakdown": risk_levels
            }
        
        return {"total_students": 0, "total_at_risk": 0, "at_risk_percentage": 0, "risk_breakdown": risk_levels}
    
    def _aggregate_resource_utilization(self, class_analytics_list: List[ClassAnalytics]) -> Dict:
        """Aggregate resource utilization across all classes"""
        # Placeholder for resource utilization aggregation
        return {
            "most_used_resources": ["Math worksheets", "Science videos", "Reading comprehension"],
            "least_used_resources": ["Audio lessons", "Interactive games"],
            "effectiveness_by_resource_type": {
                "visual": 0.78,
                "audio": 0.65,
                "interactive": 0.82,
                "text": 0.71
            }
        }
    
    def _generate_school_trends(self, class_analytics_list: List[ClassAnalytics]) -> List[str]:
        """Generate school-wide trends and insights"""
        return [
            "Student engagement has improved by 15% this month",
            "Mathematics performance shows consistent growth across all classes",
            "Science retention rates need attention in grades 4-6",
            "Interactive content shows 23% higher engagement than traditional methods"
        ]
    
    def _generate_admin_recommendations(self, class_analytics_list: List[ClassAnalytics], language: Language) -> List[str]:
        """Generate recommendations for school administrators"""
        if language == Language.ENGLISH:
            return [
                "Invest in more interactive science learning materials",
                "Provide additional training for teachers with effectiveness scores below 0.6",
                "Implement peer tutoring program to support at-risk students",
                "Consider adjusting Monday lesson plans based on engagement patterns"
            ]
        else:
            return [
                "Wekeza katika vifaa vya kujifunza sayansi vya kuingiliana zaidi",
                "Toa mafunzo ya ziada kwa walimu wenye alama za ufanisi chini ya 0.6",
                "Tekeleza programu ya ufundishaji wa kijana kwa kijana kusaidia wanafunzi walio hatarini",
                "Fikiria kurekebisha mipango ya masomo ya Jumatatu kulingana na mielekeo ya ushiriki"
            ]
    
    # Additional helper methods
    def _identify_favorite_subjects(self, report_data: Dict) -> List[str]:
        """Identify student's favorite subjects based on engagement and performance"""
        subject_scores = {}
        
        for subject, retention in report_data["retention_rate"].items():
            velocity = report_data["learning_velocity"].get(subject, 0)
            # Combine retention and velocity for preference score
            preference_score = (retention * 0.7) + (min(velocity, 2) / 2 * 0.3)
            subject_scores[subject] = preference_score
        
        # Return top 2 subjects
        sorted_subjects = sorted(subject_scores.items(), key=lambda x: x[1], reverse=True)
        return [subject for subject, score in sorted_subjects[:2]]
    
    def _describe_study_habits(self, report_data: Dict, language: Language) -> str:
        """Describe student's study habits in simple terms"""
        engagement = report_data["engagement_score"]
        
        if engagement["frequency"] >= 0.7 and engagement["completion"] >= 0.7:
            return "Regular and focused study sessions" if language == Language.ENGLISH else "Vipindi vya kusoma vya kawaida na vya umakini"
        elif engagement["frequency"] >= 0.5:
            return "Studying several times per week" if language == Language.ENGLISH else "Kusoma mara kadhaa kwa wiki"
        else:
            return "Irregular study pattern" if language == Language.ENGLISH else "Muundo usio wa kawaida wa kusoma"
    
    def _identify_recent_achievements(self, report_data: Dict) -> List[str]:
        """Identify recent achievements to highlight"""
        achievements = []
        
        # High learning velocity in any subject
        for subject, velocity in report_data["learning_velocity"].items():
            if velocity >= 1.0:
                achievements.append(f"Making fast progress in {subject}")
        
        # High retention rates
        for subject, retention in report_data["retention_rate"].items():
            if retention >= 0.85:
                achievements.append(f"Excellent retention in {subject}")
        
        # High engagement
        if report_data["engagement_score"]["overall"] >= 0.8:
            achievements.append("Consistent and engaged learning")
        
        return achievements[:3]  # Top 3 achievements