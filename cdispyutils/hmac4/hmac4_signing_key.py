"""
Provides HMAC4SigningKey class for generating Hmac signature.
This class inspired by AWS4SigningKey from requests_aws4auth

"""

# Licensed under the MIT License:
# http://opensource.org/licenses/MIT




import hmac
import hashlib
from warnings import warn
from datetime import datetime
from six import text_type
from .. import constants


class HMAC4SigningKey:
    """
    HMAC signing key. Used to sign HMAC authentication strings.

    The secret key is stored in the instance after instantiation, this can be
    changed via the store_secret_key argument, see below for details.

    Methods:
    generate_key() -- Generate AWS4 Signing Key string
    sign_sha256()  -- Generate SHA256 HMAC signature, encoding message to bytes
                      first if required

    Attributes:
    region   -- AWS region the key is scoped for
    service  -- AWS service the key is scoped for
    date     -- Date the key is scoped for
    key      -- The signing key string itself

    amz_date -- Deprecated name for 'date'. Use the 'date' attribute instead.
                amz_date will be removed in a future version.

    """

    def __init__(self, secret_key, service, prefix=None, postfix=None,
                 region=None, date=None, store_secret_key=True):
        """
        >>> HMAC4SigningKey(secret_key, service[, date]
        ...                [, store_secret_key])

        secret_key -- This is your HMAC secret access key
        service    -- The name of the service you're connecting to, as per
                      endpoints at:
                      http://docs.aws.amazon.com/general/latest/gr/rande.html
                      e.g. elasticbeanstalk
        date       -- Date of the form %Y%m%d. Key is only valid for
                      requests with a Date or X-Amz-Date header matching this
                      date. If date is not supplied the current date is
                      used.
        store_secret_key
                   -- Whether the secret key is stored in the instance. By
                      default this is True, meaning the key is stored in
                      the secret_key property and is available to any
                      code the instance is passed to. Having the secret
                      key retained makes it easier to regenerate the key
                      if a scope parameter changes (usually the date).
                      This is used by the AWS4Auth class to perform its
                      automatic key updates when a request date/scope date
                      mismatch is encountered.

                      If you are passing instances to untrusted code you can
                      set this to False. This will cause the secret key to be
                      discarded as soon as the signing key has been generated.
                      Note though that you will need to manually regenerate
                      keys when needed (or if you use the regenerate_key()
                      method on an AWS4Auth instance you will need to pass it
                      the secret key).

        All arguments should be supplied as strings.

        """

        self.service = service
        self.region = region
        self.prefix = prefix or "HMAC4"
        self.postfix = postfix or 'hmac4_request'
        self.short_date_stamp = date or datetime.utcnow().strftime(constants.ABRIDGED_DATE_TIME_FORMAT)
        self.store_secret_key = store_secret_key
        self.secret_key = secret_key if self.store_secret_key else None
        self.key = self.generate_key(self.prefix, self.postfix,
                                     self.secret_key, self.service,
                                     self.short_date_stamp, self.region)

    @classmethod
    def generate_key(cls, prefix, postfix, secret_key, service, date, region=None):
        """
        Generate the signing key string as bytes.

        If intermediate is set to True, returns a 4-tuple containing the key
        and the intermediate keys:

        ( signing_key, date_key, region_key, service_key )

        The intermediate keys can be used for testing against examples from
        Amazon.

        """
        init_key = (prefix + secret_key).encode('utf-8')
        date_key = cls.sign_sha256(init_key, date)
        region_key = date_key if region is None else cls.sign_sha256(date_key, region)
        service_key = cls.sign_sha256(region_key, service)
        key = cls.sign_sha256(service_key, postfix)
        return key

    @staticmethod
    def sign_sha256(key, msg):
        """
        Generate an SHA256 HMAC, encoding msg to UTF-8 if not
        already encoded.

        key -- signing key. bytes.
        msg -- message to sign. unicode or bytes.

        """
        if isinstance(msg, text_type):
            msg = msg.encode('utf-8')
        return hmac.new(key, msg, hashlib.sha256).digest()

    @property
    def amz_date(self):
        msg = ("This attribute has been renamed to 'date'. 'amz_date' is "
               "deprecated and will be removed in a future version.")
        warn(msg, DeprecationWarning)
        return self.short_date_stamp
