from flask import Blueprint, render_template, request, flash, redirect, url_for
from outreach_pilot.models import EmailTemplate
from outreach_pilot.extensions import db
from outreach_pilot.auth.utils import login_required

templates_bp = Blueprint('template_manager', __name__)

@templates_bp.route('/')
@login_required
def list_templates():
    templates = EmailTemplate.query.all()
    return render_template('templates.html', templates=templates)

@templates_bp.route('/new')
@login_required
def new_template_form():
    return render_template('create_template.html')

@templates_bp.route('/create', methods=['POST'])
@login_required
def create_template():
    subject = request.form.get('subject')
    body = request.form.get('body')
    if subject and body:
        try:
            db.session.add(EmailTemplate(subject=subject, body=body, is_default=False))
            db.session.commit()
            flash("New template created successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating template: {e}", "danger")
        return redirect(url_for('templates.list_templates'))
    flash("Error: Both subject and body are required.", "warning")
    return redirect(url_for('templates.new_template_form'))

@templates_bp.route('/<int:template_id>/edit')
@login_required
def edit_template_form(template_id):
    template = EmailTemplate.query.get_or_404(template_id)
    return render_template('edit_template.html', template=template)

@templates_bp.route('/<int:template_id>/update', methods=['POST'])
@login_required
def update_template(template_id):
    template = EmailTemplate.query.get_or_404(template_id)
    subject = request.form.get('subject')
    body = request.form.get('body')
    if subject and body:
        try:
            template.subject = subject
            template.body = body
            db.session.commit()
            flash('Template updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating template: {e}', 'danger')
        return redirect(url_for('templates.list_templates'))
    flash('Error: Both subject and body are required.', 'warning')
    return redirect(url_for('templates.edit_template_form', template_id=template_id))

@templates_bp.route('/<int:template_id>/delete', methods=['POST'])
@login_required
def delete_template(template_id):
    template = EmailTemplate.query.get_or_404(template_id)
    if template.is_default:
        flash('Error: Cannot delete default templates.', 'danger')
        return redirect(url_for('templates.list_templates'))

    try:
        db.session.delete(template)
        db.session.commit()
        flash('Template deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting template: {e}', 'danger')
    return redirect(url_for('templates.list_templates'))

