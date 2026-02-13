"""
Admin routes for user management and usage statistics.
"""
from flask import Blueprint, render_template, redirect, url_for, flash
from app.auth import requires_admin, get_current_user
from app.database import get_all_users, get_user, delete_user, update_user_field, get_admin_stats

admin = Blueprint("admin", __name__, url_prefix="/admin")


@admin.route("/")
@requires_admin
def admin_dashboard():
    """Admin dashboard with user list and stats."""
    users = get_all_users()
    stats = get_admin_stats()
    current_user = get_current_user()
    return render_template("admin/dashboard.html", users=users, stats=stats,
                           current_user=current_user)


@admin.route("/user/<int:user_id>/toggle-disable", methods=["POST"])
@requires_admin
def toggle_disable(user_id):
    """Enable or disable a user account."""
    user = get_user(user_id)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("admin.admin_dashboard"))

    current_user = get_current_user()
    if user["id"] == current_user["id"]:
        flash("You cannot disable your own account.", "error")
        return redirect(url_for("admin.admin_dashboard"))

    new_status = 0 if user["is_disabled"] else 1
    update_user_field(user_id, "is_disabled", new_status)

    action = "disabled" if new_status else "enabled"
    name = f"{user['firstname'] or ''} {user['lastname'] or ''}".strip() or user['email'] or f"User #{user_id}"
    flash(f"Account for {name} has been {action}.", "success")
    return redirect(url_for("admin.admin_dashboard"))


@admin.route("/user/<int:user_id>/delete", methods=["POST"])
@requires_admin
def admin_delete_user(user_id):
    """Delete a user account."""
    user = get_user(user_id)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("admin.admin_dashboard"))

    current_user = get_current_user()
    if user["id"] == current_user["id"]:
        flash("You cannot delete your own account.", "error")
        return redirect(url_for("admin.admin_dashboard"))

    name = f"{user['firstname'] or ''} {user['lastname'] or ''}".strip() or user['email'] or f"User #{user_id}"
    delete_user(user_id)
    flash(f"User {name} has been deleted.", "success")
    return redirect(url_for("admin.admin_dashboard"))


@admin.route("/user/<int:user_id>/toggle-admin", methods=["POST"])
@requires_admin
def toggle_admin(user_id):
    """Grant or revoke admin privileges."""
    user = get_user(user_id)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("admin.admin_dashboard"))

    current_user = get_current_user()
    if user["id"] == current_user["id"]:
        flash("You cannot change your own admin status.", "error")
        return redirect(url_for("admin.admin_dashboard"))

    new_status = 0 if user["is_admin"] else 1
    update_user_field(user_id, "is_admin", new_status)

    action = "granted" if new_status else "revoked"
    name = f"{user['firstname'] or ''} {user['lastname'] or ''}".strip() or user['email'] or f"User #{user_id}"
    flash(f"Admin privileges {action} for {name}.", "success")
    return redirect(url_for("admin.admin_dashboard"))
