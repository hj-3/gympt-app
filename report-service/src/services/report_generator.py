"""
Report generation service using ReportLab
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image as RLImage,
)
from reportlab.pdfgen import canvas
from datetime import datetime
from typing import Dict, List, Optional
import io
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from io import BytesIO


class ReportGenerator:
    """Generate PDF workout reports"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1E40AF'),
            spaceAfter=30,
            alignment=1,  # Center
        ))

        # Heading style
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1E40AF'),
            spaceAfter=12,
        ))

        # Body style
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText'],
            fontSize=12,
            spaceAfter=12,
        ))

    def generate_workout_report(
        self,
        user_name: str,
        workout_data: Dict,
        historical_data: Optional[List[Dict]] = None,
        ai_insights: Optional[str] = None,
    ) -> BytesIO:
        """
        Generate comprehensive workout report

        Args:
            user_name: User's name
            workout_data: Current workout session data
            historical_data: Previous workout sessions
            ai_insights: AI-generated insights

        Returns:
            BytesIO buffer containing PDF
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )

        # Build story (content)
        story = []

        # Title
        story.append(Paragraph(
            f"GYMPT Workout Report",
            self.styles['CustomTitle']
        ))
        story.append(Paragraph(
            f"User: {user_name}",
            self.styles['CustomHeading']
        ))
        story.append(Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            self.styles['CustomBody']
        ))
        story.append(Spacer(1, 0.3 * inch))

        # Session Summary
        story.append(Paragraph("Session Summary", self.styles['CustomHeading']))
        summary_data = [
            ["Metric", "Value"],
            ["Duration", f"{workout_data.get('durationMinutes', 0)} minutes"],
            ["Exercises Completed", str(workout_data.get('exercisesCompleted', 0))],
            ["Total Reps", str(workout_data.get('totalReps', 0))],
            ["Average Form Score", f"{workout_data.get('avgFormScore', 0):.1f}/10"],
            ["Calories Burned", f"{workout_data.get('caloriesBurned', 0)} kcal"],
        ]

        summary_table = Table(summary_data, colWidths=[3 * inch, 3 * inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E40AF')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.3 * inch))

        # Exercise Breakdown
        if 'exercises' in workout_data and workout_data['exercises']:
            story.append(Paragraph("Exercise Breakdown", self.styles['CustomHeading']))

            exercise_data = [["Exercise", "Sets", "Reps", "Avg Form Score"]]
            for exercise in workout_data['exercises']:
                exercise_data.append([
                    exercise.get('exerciseName', 'Unknown'),
                    str(exercise.get('sets', 0)),
                    str(exercise.get('reps', 0)),
                    f"{exercise.get('avgFormScore', 0):.1f}/10",
                ])

            exercise_table = Table(exercise_data, colWidths=[2 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])
            exercise_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E40AF')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(exercise_table)
            story.append(Spacer(1, 0.3 * inch))

        # Progress Chart
        if historical_data and len(historical_data) > 1:
            story.append(Paragraph("Progress Over Time", self.styles['CustomHeading']))
            chart_image = self._generate_progress_chart(historical_data)
            if chart_image:
                story.append(RLImage(chart_image, width=5 * inch, height=3 * inch))
                story.append(Spacer(1, 0.3 * inch))

        # AI Insights
        if ai_insights:
            story.append(PageBreak())
            story.append(Paragraph("AI Coach Insights", self.styles['CustomHeading']))
            story.append(Paragraph(ai_insights, self.styles['CustomBody']))
            story.append(Spacer(1, 0.2 * inch))

        # Recommendations
        story.append(Paragraph("Recommendations for Next Workout", self.styles['CustomHeading']))
        recommendations = self._generate_recommendations(workout_data, historical_data)
        for rec in recommendations:
            story.append(Paragraph(f"• {rec}", self.styles['CustomBody']))

        # Footer
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph(
            "Keep up the great work! Your consistency is key to achieving your fitness goals.",
            self.styles['CustomBody']
        ))
        story.append(Paragraph(
            "Generated by GYMPT AI Personal Trainer",
            ParagraphStyle(
                name='Footer',
                parent=self.styles['BodyText'],
                fontSize=10,
                textColor=colors.grey,
                alignment=1,
            )
        ))

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer

    def _generate_progress_chart(self, historical_data: List[Dict]) -> Optional[BytesIO]:
        """Generate progress chart using matplotlib"""
        try:
            # Extract data
            dates = []
            form_scores = []
            durations = []

            for session in historical_data[-10:]:  # Last 10 sessions
                date_str = session.get('sessionDate', '')
                if date_str:
                    dates.append(datetime.fromisoformat(date_str.replace('Z', '+00:00')).strftime('%m/%d'))
                else:
                    dates.append('N/A')

                form_scores.append(session.get('avgFormScore', 0))
                durations.append(session.get('durationMinutes', 0))

            # Create figure
            fig, ax1 = plt.subplots(figsize=(8, 4))

            # Plot form scores
            color = 'tab:blue'
            ax1.set_xlabel('Date')
            ax1.set_ylabel('Avg Form Score', color=color)
            ax1.plot(dates, form_scores, color=color, marker='o', label='Form Score')
            ax1.tick_params(axis='y', labelcolor=color)
            ax1.set_ylim([0, 10])

            # Plot duration on secondary axis
            ax2 = ax1.twinx()
            color = 'tab:orange'
            ax2.set_ylabel('Duration (min)', color=color)
            ax2.plot(dates, durations, color=color, marker='s', label='Duration')
            ax2.tick_params(axis='y', labelcolor=color)

            # Title and grid
            plt.title('Workout Progress')
            ax1.grid(True, alpha=0.3)
            plt.tight_layout()

            # Save to buffer
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            plt.close(fig)

            return buffer

        except Exception as e:
            print(f"Error generating chart: {e}")
            return None

    def _generate_recommendations(
        self,
        workout_data: Dict,
        historical_data: Optional[List[Dict]],
    ) -> List[str]:
        """Generate workout recommendations based on data"""
        recommendations = []

        avg_form_score = workout_data.get('avgFormScore', 0)

        # Form score based recommendations
        if avg_form_score < 6:
            recommendations.append(
                "Focus on form quality over quantity. Consider lowering weight/reps to perfect your technique."
            )
        elif avg_form_score >= 8:
            recommendations.append(
                "Excellent form! You're ready to progress to more challenging variations or increase intensity."
            )

        # Duration based recommendations
        duration = workout_data.get('durationMinutes', 0)
        if duration < 20:
            recommendations.append(
                "Try to extend your workout duration to 30-45 minutes for optimal results."
            )
        elif duration > 90:
            recommendations.append(
                "Great endurance! Make sure you're allowing adequate recovery time between sessions."
            )

        # Consistency based recommendations
        if historical_data and len(historical_data) >= 3:
            recent_sessions = historical_data[-7:]  # Last 7 sessions
            if len(recent_sessions) >= 3:
                recommendations.append(
                    f"You've completed {len(recent_sessions)} workouts recently. Great consistency!"
                )
            else:
                recommendations.append(
                    "Try to maintain 3-4 workouts per week for best results."
                )

        # Default recommendation
        if not recommendations:
            recommendations.append(
                "Keep up the good work! Consistency is key to achieving your fitness goals."
            )

        return recommendations


class ReportMetadata:
    """Report metadata for tracking"""

    def __init__(
        self,
        user_id: str,
        session_id: str,
        report_type: str,
    ):
        self.user_id = user_id
        self.session_id = session_id
        self.report_type = report_type
        self.generated_at = datetime.now().isoformat()
        self.report_id = f"{user_id}_{session_id}_{int(datetime.now().timestamp())}"
        self.s3_key = f"reports/{user_id}/{self.report_id}.pdf"

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "report_id": self.report_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "report_type": self.report_type,
            "generated_at": self.generated_at,
            "s3_key": self.s3_key,
        }
