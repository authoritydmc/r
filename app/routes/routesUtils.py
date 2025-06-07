from functools import wraps

from flask import session, request, jsonify, redirect, url_for

import logging

logger=logging.getLogger(__name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            logger.warning(f"Authentication required for {request.path}. User not logged in.")
            # If AJAX/JSON request, return JSON error
            if request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']:
                return jsonify({'success': False, 'error': 'Authentication required'}), 401
            # Otherwise, redirect to login page
            return redirect(url_for('main.admin_login', next=request.path))
        logger.debug(f"User authenticated for {request.path}.")
        return f(*args, **kwargs)

    return decorated_function
