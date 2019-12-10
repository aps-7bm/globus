import log_lib
import globus_sdk

__author__ = "Francesco De Carlo"
__copyright__ = "Copyright (c) 2019, UChicago Argonne, LLC."
__version__ = "0.0.1"
__docformat__ = 'restructuredtext en'

__all__ = ['create_clients',
           'create_dir',
           'share_dir']

def show_endpoints(args, ac, tc):

    log_lib.info('Show all endpoints shared and owned by my globus user credentials')
    log_lib.info("*** Endpoints shared with me:")
    for ep in tc.endpoint_search(filter_scope="shared-with-me"):
        log_lib.info("*** *** [{}] {}".format(ep["id"], ep["display_name"]))
    log_lib.info("*** Endpoints owned with me::")
    for ep in tc.endpoint_search(filter_scope="my-endpoints"):
         log_lib.info("*** *** [{}] {}".format(ep["id"], ep["display_name"]))


def create_clients(app_id):
  """
  Create authorize and transfer clients

  Parameters
  ----------
  app_id : App UUID 

  Returns
  -------
  ac : Authorize client
  tc : Transfer client
    
    """

  client = globus_sdk.NativeAppAuthClient(app_id)
  client.oauth2_start_flow(refresh_tokens=True)

  log_lib.warning('Please go to this URL and login: {0}'.format(client.oauth2_get_authorize_url()))

  get_input = getattr(__builtins__, 'raw_input', input)
  auth_code = get_input('Please enter the code you get after login here: ').strip() # pythn 3
  # auth_code = raw_input('Please enter the code you get after login here: ').strip() # python 2.7
  
  token_response = client.oauth2_exchange_code_for_tokens(auth_code)

  # let's get stuff for the Globus Transfer service
  globus_transfer_data = token_response.by_resource_server['transfer.api.globus.org']
  # the refresh token and access token, often abbr. as RT and AT
  transfer_rt = globus_transfer_data['refresh_token']
  transfer_at = globus_transfer_data['access_token']
  expires_at_s = globus_transfer_data['expires_at_seconds']

  # Now we've got the data we need, but what do we do?
  # That "GlobusAuthorizer" from before is about to come to the rescue
  authorizer = globus_sdk.RefreshTokenAuthorizer(transfer_rt, client, access_token=transfer_at, expires_at=expires_at_s)
  # and try using `tc` to make TransferClient calls. Everything should just
  # work -- for days and days, months and months, even years
  ac = globus_sdk.AuthClient(authorizer=authorizer)
  tc = globus_sdk.TransferClient(authorizer=authorizer)

  return ac, tc


# def create_user_dirs(args,
#                     ac,              # Authorize client  
#                     tc):             # Transfer client

#     date_dir_path = args.globus_server_top_dir + args.year_month + '/'
#     pi_last_name_dir_path = args.globus_server_top_dir + args.year_month + '/' + args.pi_last_name + '/'

#     try:
#       response = tc.operation_mkdir(args.globus_server_uuid, path=date_dir_path)
#       log_lib.info('*** Created folder: %s' % date_dir_path)
#       response = tc.operation_mkdir(args.globus_server_uuid, path=pi_last_name_dir_path)
#       log_lib.info('*** Created folder: %s' % pi_last_name_dir_path)
#       return True
#     except:
#       log_lib.warning('*** Path %s or %s already exists' % (date_dir_path, pi_last_name_dir_path))
#       return False


def create_user_dirs(args,
                    ac,              # Authorize client  
                    tc):             # Transfer client

    date_dir_path = args.globus_server_top_dir + args.year_month + '/'
    pi_last_name_dir_path = args.globus_server_top_dir + args.year_month + '/' + args.pi_last_name + '/'

    try:
      response = tc.operation_mkdir(args.globus_server_uuid, path=date_dir_path)
      log_lib.info('*** Created folder: %s' % date_dir_path)
    except:
      log_lib.warning('*** Path %s already exists' % (date_dir_path))

    try:
      response = tc.operation_mkdir(args.globus_server_uuid, path=pi_last_name_dir_path)
      log_lib.info('*** Created folder: %s' % pi_last_name_dir_path)
      return True
    except:
      log_lib.warning('*** Path %s already exists' % (pi_last_name_dir_path))
      return False


def create_dir(directory,       # Subdirectory name under top to be created
               args,
               ac,              # Authorize client  
               tc):             # Transfer client

    new_dir_path = args.globus_server_top_dir + directory + '/'

    try:
      response = tc.operation_mkdir(args.globus_server_uuid, path=new_dir_path)
      log_lib.info('*** Created folder: %s' % new_dir_path)
      return True
    except:
      log_lib.warning('*** Path %s already exists' % new_dir_path)
      return False


def share_dir(directory,      # Subdirectory name under top to be shared with user email address
              args,
              ac,             # Authorize client  
              tc):            # Transfer client

    # Generate user id from user email
    r = ac.get_identities(usernames=args.pi_email)
    user_id = r['identities'][0]['id']
    # log_lib.info(r, user_id)

    directory_full_path = args.globus_server_top_dir + directory + '/'
    # Set access control and notify user
    rule_data = {
      'DATA_TYPE': 'access',
      'principal_type': 'identity',
      'principal': user_id,
      'path': directory_full_path,
      'permissions': 'r',
      'notify_email': args.pi_email,
      'notify_message': args.globus_message
    }

    try: 
      response = tc.add_endpoint_acl_rule(args.globus_server_uuid, rule_data)
      log_lib.info('*** Path %s has been shared with %s' % (directory_full_path, args.pi_email))
      return True
    except:
      log_lib.warning('*** Path %s is already shared with %s' % (directory_full_path, args.pi_email))
      return False


