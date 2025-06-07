import re
from datetime import datetime, timezone

from flask import Blueprint, request, redirect, url_for, render_template

from app import CONSTANTS
from app.routes.routesUtils import login_required

from app.utils import utils
import logging
bp=Blueprint('redirection', __name__)
logger = logging.getLogger(__name__)


@bp.route('/delete/<path:subpath>', methods=['GET', 'POST'])
@login_required
def dashboard_delete(subpath):
    if utils.get_delete_requires_password():
        if request.method == 'POST':
            admin_pwd = utils.get_admin_password()
            if request.form.get('password') == admin_pwd:
                utils.deleteShortCut(subpath)
                logger.info(f"Shortcut '{subpath}' deleted by admin.")
                return redirect(url_for('main.dashboard'))
            else:
                error = 'Invalid password.'
                logger.warning(f"Failed delete attempt for '{subpath}' (invalid password).")
                return render_template('delete_confirm.html', error=error, subpath=subpath)
        else:
            logger.debug(f"Displaying delete confirmation for '{subpath}'.")
            return render_template('delete_confirm.html', subpath=subpath, error=None)
    else:
        logger.info(f"Shortcut '{subpath}' deleted (password not required).")
        utils.deleteShortCut(subpath)
        return redirect(url_for('main.dashboard'))

# GET/POST: Edit or create shortcut. Triggered when user visits /edit/<subpath> or submits edit form.
@bp.route('/edit/<path:subpath>', methods=['GET', 'POST'])
def edit_redirect(subpath):

    shortcut, source_data, resp_time = utils.get_shortcut(subpath)

    if request.method == 'POST':
        type_ = request.form['type']
        target = request.form['target']
        current_time = datetime.now(timezone.utc).isoformat(sep=' ', timespec='seconds')
        ip_address = request.remote_addr or 'unknown'

        try:
            utils.set_shortcut(
                pattern=subpath,
                type_=type_,
                target=target,
                created_at=current_time if not shortcut else None,
                updated_at=current_time,
                created_ip=ip_address if not shortcut else None,
                updated_ip=ip_address
            )
            logger.info(f"Shortcut '{subpath}' {'updated' if shortcut else 'created'}.")
            return render_template('success_create.html', pattern=subpath, target=target)
        except Exception as e:
            logger.exception(f"Failed to {'update' if shortcut else 'create'} shortcut '{subpath}'.")
            # You might want a different error template or message here
            return render_template('error.html', message=f"Failed to save shortcut: {e}")
    else:  # GET request
        if not shortcut:
            logger.debug(f"Displaying create shortcut page for new pattern: '{subpath}'.")
            return render_template('create_shortcut.html', pattern=subpath)
        logger.debug(f"Displaying edit shortcut page for existing pattern: '{subpath}'.")
        return render_template('edit_shortcut.html', pattern=subpath, type=shortcut['type'], target=shortcut['target'])


@bp.route('/<path:subpath>', methods=['GET'])
def handle_redirect(subpath):
    logger.info(f"Attempting to handle redirect for subpath: '{subpath}'")
    # sanitize  pattern
    pattern,dynamicProp= utils.destructureSubPath(subpath)
    shortcut, data_source, resp_time = utils.get_shortcut(pattern)
    print(shortcut,data_source,resp_time)
    if shortcut:
        if (data_source == CONSTANTS.data_source_redirect or data_source == CONSTANTS.data_source_redis) and \
                shortcut.get(CONSTANTS.KEY_DATA_TYPE) == CONSTANTS.DATA_TYPE_STATIC:
            utils.increment_access_count(subpath)
            logger.info(
                f"Redirecting static shortcut: '{subpath}' -> '{shortcut['target']}' (Source: {data_source}, Time: {resp_time:.4f}s)")
            if utils.get_auto_redirect_delay() > 0:
                return render_template('redirect.html', target=shortcut['target'], delay=utils.get_auto_redirect_delay(), source=data_source, response_time=resp_time)
            return redirect(shortcut['target'], code=302)

        # UPSTREAM _HANDLING :::
        if data_source == CONSTANTS.data_source_upstream and shortcut.get('resolved_url'):
            logger.info(
                f"Redirecting upstream shortcut: '{subpath}' -> '{shortcut['resolved_url']}' (Source: {data_source}, Time: {resp_time:.4f}s)")
            if utils.get_auto_redirect_delay() > 0:
                return render_template('redirect.html', target=shortcut['resolved_url'],
                                       delay=utils.get_auto_redirect_delay(), source=data_source,
                                       response_time=resp_time)
            return redirect(shortcut['resolved_url'], code=302)

        if (data_source == CONSTANTS.data_source_redirect or data_source == CONSTANTS.data_source_redis) and \
                shortcut.get(CONSTANTS.KEY_DATA_TYPE) == CONSTANTS.DATA_TYPE_DYNAMIC:
            target=shortcut['target']

            if subpath == pattern:
                example_var = 'yourvalue'
                example_target = utils.replacePlaceHolders(target, example_var)
                logger.info(f"Dynamic shortcut '{pattern}' accessed without variable. Showing usage instructions.")
                return render_template('dynamic_shortcut_usage.html', pattern=pattern, var_name=utils.get_placeholder_vars(target)[0],
                                       example_target=example_target)
            if subpath.startswith(pattern + "/"):
                variable = subpath[len(pattern) + 1:]
                dest_url = re.sub(r"\{\w+\}", variable, target)
                utils.increment_access_count(pattern)
                logger.info(f"Redirecting dynamic shortcut: '{subpath}' -> '{dest_url}' (Source: {data_source})")
                if utils.get_auto_redirect_delay() > 0:
                    return render_template('redirect.html', target=dest_url, delay=utils.get_auto_redirect_delay(), source=data_source)
                return redirect(dest_url, code=302)

    logger.info(f"No direct shortcut found for '{subpath}'. Checking live upstreams.")
    if utils.get_upstreams():
        first_segment = subpath.split('/')[0]
        logger.debug(f"Redirecting to upstream check UI for first segment: '{first_segment}'")
        return redirect(url_for('main.check_upstreams_ui', pattern=first_segment), code=302)

    logger.info(f"No upstreams configured. Redirecting to create shortcut page for '{subpath}'.")
    return redirect(url_for('main.edit_redirect', subpath=subpath))

@bp.route('/edit/', methods=['GET', 'POST'])
def edit_redirect_blank():
    if request.method == 'POST':
        pattern = request.form.get('pattern', '').strip()
        type_ = request.form.get('type', CONSTANTS.DATA_TYPE_STATIC)
        target = request.form.get('target', '').strip()
        current_time = datetime.utcnow().isoformat(sep=' ', timespec='seconds')
        ip_address = request.remote_addr or 'unknown'

        if not pattern:
            logger.warning("Attempted to create shortcut with empty pattern.")
            return render_template('create_shortcut.html', pattern='', error='Shortcut pattern cannot be empty.')

        if utils.isPatternExists(pattern):
            logger.warning(f"Attempted to create shortcut '{pattern}' which already exists.")
            return render_template('create_shortcut.html', pattern=pattern,
                                   error='A shortcut with this pattern already exists.')

        try:
            utils.set_shortcut(
                pattern=pattern,
                type_=type_,
                target=target,
                created_at=current_time,
                updated_at=current_time,
                created_ip=ip_address,
                updated_ip=ip_address
            )
            logger.info(f"New shortcut '{pattern}' created successfully via blank edit route.")
            return render_template('success_create.html', pattern=pattern, target=target)
        except Exception as e:
            logger.exception(f"Failed to create new shortcut '{pattern}' via blank edit route.")
            return render_template('error.html', message=f"Failed to create shortcut: {e}")

    logger.debug("Rendering blank create shortcut page.")
    return render_template('create_shortcut.html', pattern='')
