import ssl
from django.core.mail.backends.smtp import EmailBackend as SMTPBackend

class TomEmailBackend(SMTPBackend):
    """
    Custom email backend for Tom's email that handles SSL certificate issues
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Create SSL context that doesn't verify certificates
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
    
    def open(self):
        """
        Override the open method to use our custom SSL context
        """
        if self.connection:
            return None
        
        try:
            # Handle source_address properly
            connection_kwargs = {
                'host': self.host,
                'port': self.port,
                'timeout': self.timeout,
            }
            
            # Only add source_address if it's set
            if hasattr(self, 'source_address') and self.source_address:
                connection_kwargs['source_address'] = self.source_address
            
            self.connection = self.connection_class(**connection_kwargs)
            
            # Handle SSL/TLS
            if self.use_ssl:
                # For SSL connections, wrap the socket
                self.connection = self.ssl_context.wrap_socket(self.connection)
            elif self.use_tls:
                self.connection.starttls(context=self.ssl_context)
            
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            
            return self.connection
        except Exception as e:
            if not self.fail_silently:
                raise e
            return None
