# -*- coding: utf-8 -*-
import json, base64, logging, requests
from urllib.request import urlopen
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from odoo import api, models
from odoo.http import request
from odoo.addons import base
from odoo.exceptions import AccessDenied

base.models.res_users.USER_PRIVATE_FIELDS.append('oauth_access_token')
from odoo.addons.auth_signup.models.res_partner import SignupError, now
_logger = logging.getLogger(__name__)

try:
    import jwt
except ImportError:
    _logger.warning("Login with Microsoft account won't be available. Please install PyJWT python library.")
    jwt = None

def find_rsa_key(jwks, unverified_header):
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            return {
              "kty": key["kty"],
              "kid": key["kid"],
              "use": key["use"],
              "n": key["n"],
              "e": key["e"]
            }

def ensure_bytes(key):
    if isinstance(key, str):
        key = key.encode('utf-8')
    return key


def decode_value(val):
    decoded = base64.urlsafe_b64decode(ensure_bytes(val) + b'==')
    return int.from_bytes(decoded, 'big')


def rsa_pem_from_jwk(jwk):
    return RSAPublicNumbers(
        n=decode_value(jwk['n']),
        e=decode_value(jwk['e'])
    ).public_key(default_backend()).public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )


class ResUsers(models.Model):
    _inherit = 'res.users'

    def _mfa_url(self):
        try:
            return super()._mfa_url()
        except:
            return None

    @api.model
    def _signup_create_user(self, values):
        if self.env.context.get('oauth_signup') and self.env.company.auth_unauthorized_action == 'create':
            return self._create_user_from_template(values)
        return super()._signup_create_user(values)

    @api.model
    def _auth_oauth_code_validate(self, provider, code):
        auth_oauth_provider = self.env['auth.oauth.provider'].browse(provider)
        data = dict(
            code=code,
            grant_type='authorization_code',
            client_id=auth_oauth_provider.client_id,
            client_secret=auth_oauth_provider.client_secret_id,
            redirect_uri=request.httprequest.url_root + 'auth_oauth/signin',
        )
        headers = {'Accept': 'application/json'}
        token_info = requests.post(auth_oauth_provider.validation_endpoint, headers=headers, data=data).json()
        if token_info.get('error'):
            raise Exception(token_info['error'])

        access_token = token_info.get('access_token')
        if token_info.get('id_token'):
            if not jwt:
                raise AccessDenied()

            token = token_info['id_token']
            tenant_id = auth_oauth_provider.azure_tenant_id
            jwks_url = f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
            issuer_url = f"https://sts.windows.net/{tenant_id}/"
            audience = auth_oauth_provider.client_id

            jwks = json.loads(urlopen(jwks_url).read())
            unverified_header = jwt.get_unverified_header(token)
            rsa_key = find_rsa_key(jwks, unverified_header)
            public_key = rsa_pem_from_jwk(rsa_key)

            data = jwt.decode(
                token,
                public_key,
                verify=True,
                algorithms=["RS256"],
                audience=audience,
                issuer=issuer_url
            )
            #data = jwt.decode(
            #    token_info['id_token'],
            #    algorithms=['RS256'],
            #    options={'verify_signature': False}
            #)
        else:
            data = self._auth_oauth_rpc(auth_oauth_provider.data_endpoint, access_token)
        validation = {'access_token': code, **data}
        return validation

    @api.model
    def _auth_oauth_signin(self, provider, validation, params):
        if self.env.context.get('oauth_code'):
            if not validation.get('user_id'):
                if validation.get('id'):
                    validation['user_id'] = validation['id']
                elif validation.get('oid'):
                    validation['user_id'] = validation['oid']
                else:
                    raise AccessDenied()

            validation.update({
                'name': ' '.join([
                    str(validation.get('given_name')),
                    str(validation.get('family_name'))
                ]),
            })
        return super()._auth_oauth_signin(provider, validation, params)

    @api.model
    def _auth_oauth_validate(self, provider, access_token):
        if self.env.context.get('oauth_code'):
            return self._auth_oauth_code_validate(provider, access_token)
        return super(ResUsers, self)._auth_oauth_validate(provider, access_token)

    @api.model
    def auth_oauth(self, provider, params):
        if params.get('code'):
            params['access_token'] = params['code']
            self = self.with_context(oauth_code=True, oauth_signup=True)
        return super(ResUsers, self).auth_oauth(provider, params)
