from NBPackage import NBInstallPyLibSwig


class NBCrypto(object):
    swig_lib = None

    @classmethod
    def init_module(cls, conn_str):
        '''
        Initialize the crypto module before you can use the rest of the APIs to do encryption/decryption.
        Keyword arguments:
        connStr -- MongoDB connection URL string to system database. E.g. 'mongodb://mongodb:mongodb@127.0.0.1/?replicaSet=rs&connect=false'
        Return: True if succeed, False in case of error (e.g. keystore not found).
        '''
        cls.swig_lib = NBInstallPyLibSwig.CNBCryptoPythonLib()
        return cls.swig_lib.LoadKeystore(conn_str, "NGSystem")

    @classmethod
    def clean_module(cls):
        '''
        clean the crypto module before exit the process
        '''
        if cls.swig_lib:
            cls.swig_lib.ClearKeystore()

    @classmethod
    def decrypt_3des(cls, ciphertext):
        '''
        Decrypt legacy data that was encrypted using 3DES and hardcoded key.
        Keyword arguments:
        ciphertext -- legacy cipher text
        Return: decrypted data
        '''
        return cls.swig_lib.Des3Decrypt(ciphertext)

    @classmethod
    def decrypt_zip_aes(cls, ciphertext):
        '''
        Decrypt legacy data that was encrypted using AES 128 (from ZipAchieve) and hardcoded key.
        Keyword arguments:
        ciphertext -- legacy cipher text
        Return: decrypted data
        '''
        return cls.swig_lib.LegacyZipAesDecrypt(ciphertext)

    @classmethod
    def encrypt_zip_aes(cls, plaintext):
        '''
        Legacy AES 128 encryption (by ZipAchieve) and hardcoded key.
        Keyword arguments:
        plaintext -- text to encrypt
        Return: encrypted cipher text
        '''
        return cls.swig_lib.LegacyZipAesEncrypt(plaintext)

    @classmethod
    def decrypt_legacy_pbe(cls, ciphertext, password):
        '''
        Decrypt legacy data that was encrypted by com.netbrain.ng.services.common.utility.Security.Cryptography::Encryt().
        Keyword arguments:
        ciphertext -- legacy cipher text
        Return: decrypted data
        '''
        s = cls.swig_lib.LegacyPBEDecrypt(ciphertext, password)
        #note: the output is in utf-16 serialized format. descerialize it and convert to regular string.
        #check com.netbrain.ng.services.common.utility.SecurityCryptography.Encrypt(string ClearText, string EncryptionKey) for more details.
        buf = bytearray()
        buf.extend(map(ord, s))
        u = buf.decode("utf-16")
        return u

    @classmethod
    def encrypt_aes_ks(cls, plaintext):
        '''
        Encrypt data using AES256 and key defined in keystore.
        Keyword arguments:
        plaintext -- raw data to encrypt
        Return: encrypted data encoded by base64
        '''
        return cls.swig_lib.KSEncrypt(plaintext)
        
    @classmethod
    def decrypt_aes_ks(cls, ciphertext):
        '''
        Deccrypt data using AES256 and key defined in keystore.
        Keyword arguments:
        ciphertext -- cipher text to decrypt
        Return: decrypted data
        '''
        return cls.swig_lib.KSDecrypt(ciphertext)
        
    @classmethod
    def spooky_hash(cls, text):
        '''
        Calculate spooky hash checksum data for input data.
        Keyword arguments:
        text -- input data
        Return: hash string
        '''
        return cls.swig_lib.Hash_Spooky(text)
 


