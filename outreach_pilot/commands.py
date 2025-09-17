import click
import textwrap
from flask.cli import with_appcontext
from .extensions import db
from .models import EmailTemplate

@click.command(name='init-db')
@with_appcontext
def init_db_command():
    """Clear existing data and create new tables."""
    db.drop_all()
    db.create_all()
    click.echo('Initialized the database.')

@click.command(name='seed-defaults')
@with_appcontext
def seed_defaults_command():
    """Seed the database with the full set of default email templates."""
    
    signature_html = textwrap.dedent("""
    <table cellpadding="0" cellspacing="0" border="0" style="margin-top: 20px; border-collapse: collapse; font-family: Verdana, sans-serif; font-size: 14px; color: #333;">
        <tr>
            <td style="vertical-align: top;">
                <strong>CloudZon Team</strong><br>
                Montu Patel – Sales Manager | <a href="mailto:montu@cloudzon.com" style="color: #1a0dab;">montu@cloudzon.com</a><br>
                R Bharucha – Transcription Head | <a href="mailto:rbharucha@cloudzon.com" style="color: #1a0dab;">rbharucha@cloudzon.com</a>
            </td>
        </tr>
    </table>
    """)


    def format_email_body(body_content):
        dedented_body = textwrap.dedent(body_content)
        return f'<div style="font-family: Verdana, sans-serif; font-size: 14px; color: #333;">{dedented_body}{signature_html}</div>'

    DEFAULT_TEMPLATES = [
        {
            "subject": "Introducing iTranscript360: AI + Human Powered Medical Transcription",
            "body": format_email_body("""
            <p>Hi {dr_name},</p>
            <p>I am pleased to introduce iTranscript360, an AI + human powered medical transcription service designed to help healthcare professionals reduce documentation time and focus more on patient care.</p>
            <p><strong>Key Features:</strong></p>
            <ul>
                <li><strong>AI Transcription</strong> – Fast and accurate output with direct PDF downloads.</li>
                <li><strong>Live Transcription</strong> – Instant, accurate transcription with customised templates.</li>
                <li><strong>HIPAA & GDPR Compliance</strong> – Full data security and regulatory compliance.</li>
                <li><strong>EHR Integration</strong> – Seamlessly integrates with your existing systems.</li>
            </ul>
            <p>Doctors using iTranscript360 save hours each week without compromising on accuracy or quality.</p>
            <p>Would you be open to a 5-minute demo? Please let me know a convenient time, and I will be happy to schedule it.</p>
            <p>Looking forward to your response.</p>
            """)
        },
        {
            "subject": "Following up on iTranscript360 – AI + Human Powered Medical Transcription",
            "body": format_email_body("""
            <p>Hi {dr_name},</p>
            <p>I hope this message finds you well. I wanted to kindly follow up on my previous email introducing iTranscript360, our AI + human-powered medical transcription service.</p>
            <p>With features like live &amp; AI transcription, customised templates, and seamless EHR integration, doctors using our service save hours each week.</p>
            <p>Would you be available for a short 5-minute demo this week to see how it could support your practice?</p>
            <p>Looking forward to your response.</p>
            """)
        },
        {
            "subject": "Just checking in – iTranscript360 demo availability",
            "body": format_email_body("""
            <p>Hi {dr_name},</p>
            <p>I wanted to follow up once more regarding iTranscript360. Many of our current doctor clients have found it incredibly helpful in:</p>
            <ul>
                <li>Reducing documentation time by up to 60%</li>
                <li>Improving accuracy in complex notes with AI + human review</li>
                <li>Freeing up hours each week for more patient interaction</li>
            </ul>
            <p>I’d love to give you a quick 5-minute demo so you can see how it works in real time. Could we schedule a convenient slot this week?</p>
            <p>Looking forward to your response.</p>
            """)
        },
        {
            "subject": "How doctors are saving hours each week with iTranscript360",
            "body": format_email_body("""
            <p>Hi {dr_name},</p>
            <p>Did you know most doctors using iTranscript360 save an average of 3–5 hours every week on documentation?</p>
            <p>Here’s why:</p>
            <ul>
                <li>AI + Human review ensures reliable notes every time</li>
                <li>Templates tailored to each speciality</li>
                <li>Instant PDF downloads and EHR-ready outputs</li>
            </ul>
            <p>That’s more time you could spend focusing on patient care rather than paperwork.</p>
            <p>Would you like me to set up a quick 5-minute demo so you can see how it works?</p>
            <p>Looking forward to your response.</p>
            """)
        },
        {
            "subject": "Secure, compliant, and faster transcription with iTranscript360",
            "body": format_email_body("""
            <p>Hi {dr_name},</p>
            <p>I wanted to highlight how iTranscript360 ensures both speed and compliance for medical transcription.</p>
            <ul>
                <li><strong>HIPAA &amp; GDPR Compliant</strong> – keeping patient data fully secure</li>
                <li><strong>24/7 Support</strong> – so you’re never left waiting</li>
                <li><strong>AI + Human Accuracy</strong> – combining the best of both worlds</li>
            </ul>
            <p>This means you don’t have to choose between accuracy and compliance — you get both.</p>
            <p>Would you be open to scheduling a short demo this week?</p>
            <p>Looking forward to your response.</p>
            """)
        },
        {
            "subject": "Limited Offer – 30% Off + 7 Days Free Trial of iTranscript360",
            "body": format_email_body("""
            <p>Hi {dr_name},</p>
            <p>I wanted to reach out one last time to share an exclusive opportunity to try iTranscript360 risk-free.</p>
            <p>For a limited time, we are offering:</p>
            <ul>
                <li>✨ 30% OFF on your subscription</li>
                <li>✨ 7-Day Free Trial – experience all features with no commitment</li>
            </ul>
            <p>Doctors using our platform save 3–5 hours per week and reduce documentation workload without compromising quality.</p>
            <p>Would you like me to share the pricing plans and set up your free trial today?</p>
            <p>Looking forward to your response.</p>
            """)
        },
        {
            "subject": "Affordable Medical Transcription – Starting at Minimum Price",
            "body": format_email_body("""
            <p>Hi {dr_name},</p>
            <p>I understand cost is an important factor, which is why iTranscript360 is designed to be both affordable and high-quality.</p>
            <p>Our services now start at a very minimum price, making it easier for doctors and clinics of any size to benefit from:</p>
            <ul>
                <li>AI + Human Accuracy at a fraction of the usual cost</li>
                <li>Flexible pricing plans to match your practice needs</li>
                <li>7-Day Free Trial so you can test the service with no risk</li>
            </ul>
            <p>We’ve ensured that our pricing remains competitive and budget-friendly, without compromising on accuracy, speed, or security.</p>
            <p>💡 Would you like me to share our most affordable pricing plan and set up your free trial right away?</p>
            <p>Looking forward to your response.</p>
            """)
        },
        {
            "subject": "Ready to disrupt your transcription process?",
            "body": format_email_body("""
            <p>Hi {dr_name},</p>
            <p>I wanted to quickly follow up and see if you had a chance to review my earlier note about iTranscript360.</p>
            <p>With setup in under 20 minutes, 40–60% savings, and tools like digital dictation &amp; online editing, our platform is already helping practices replace old, slow transcription workflows.</p>
            <p>👉 Can I schedule a quick 15-min call to show you how it works in real time?</p>
            <p>Looking forward to your response.</p>
            """)
        },
        {
            "subject": "Still using traditional transcription? Let’s change that.",
            "body": format_email_body("""
            <p>Hi {dr_name},</p>
            <p>Healthcare is moving fast. Traditional transcription is too slow, too costly, and too rigid.</p>
            <p>That’s why more practices are switching to iTranscript360 — the platform that:</p>
            <ul>
                <li>Cuts transcription costs by up to 60%</li>
                <li>Adapts to your workflow instantly</li>
                <li>Gets you started the same day you sign up</li>
            </ul>
            <p>This isn’t about small improvements — it’s about reinventing transcription.</p>
            <p>👉 Would you be open to a short demo this week?</p>
            <p>Looking forward to your response.</p>
            """)
        },
        {
            "subject": "Last chance – Should I close your file?",
            "body": format_email_body("""
            <p>Hi {dr_name},</p>
            <p>I don’t want to keep filling your inbox, so this will be my last note.</p>
            <p>If now isn’t the right time, no worries — just let me know, and I’ll close your file. But if you’re curious to see how you can save 40–60% and move to a smarter transcription process, I would be happy to set up a demo for you.</p>
            <p>Looking forward to your decision.</p>
            """)
        },
        {
            "subject": "Final reminder – Don’t miss out on iTranscript360 benefits",
            "body": format_email_body("""
            <p>Hi {dr_name},</p>
            <p>This will be my final reminder about iTranscript360. Many practices are already saving significant time and costs — and I’d hate for you to miss out.</p>
            <p>With iTranscript360 you get:</p>
            <ul>
                <li>40–60% savings compared to traditional transcription</li>
                <li>Setup in less than 20 minutes</li>
                <li>Custom templates and full EHR integration</li>
            </ul>
            <p>If now isn’t the right time, no problem — just let me know, and I won’t reach out again. But if you’d like to explore how this could help your practice, I’d be happy to set up a quick demo.</p>
            <p>Looking forward to your response.</p>
            """)
        }
    ]

    if EmailTemplate.query.filter_by(is_default=True).count() > 0:
        click.echo('Default templates already exist. Deleting them to re-seed.')
        EmailTemplate.query.filter_by(is_default=True).delete()
        db.session.commit()

    for t in DEFAULT_TEMPLATES:
        db.session.add(EmailTemplate(subject=t['subject'], body=t['body'], is_default=True))
    db.session.commit()
    click.echo(f'Successfully seeded {len(DEFAULT_TEMPLATES)} new default templates.')
