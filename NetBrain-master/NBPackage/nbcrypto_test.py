from nbcrypto import NBCrypto

 

if __name__ == "__main__":

    print("test NBCryto...")
    NBCrypto.clean_module()
    connect_str = "mongodb://admin:admin@192.168.48.203/?replicaSet=rs&connect=false"
    connect_str = "mongodb://admin:Netbrain1!@192.168.31.95/admin?authMechanism=SCRAM-SHA-256&ssl=true&sslAllowInvalidCertificates=true&ssl_cert_reqs=CERT_NONE"
    #connect_str = "mongodb://admin:Netbrain1!@192.168.31.95/?replicaSet=rs&connect=false&sslAllowInvalidCertificates=true&authMechanism=SCRAM-SHA-256&ssl=true&ssl_cert_reqs=CERT_NONE"
    if not NBCrypto.init_module(connect_str):
        print('NBCrypto.init_module failed')
    #test decrypt legacy 3DES encrypted data
    ciphertext2 = "jrJ2dxmOGDw=" #from NGSystem.TenantConnection. Expects "mongodb".
    deciphertext2 = NBCrypto.decrypt_3des(ciphertext2)
    print("3DES: expects=> {}, decipher result=> {}".format("mongodb", deciphertext2))

    #test decrypt legacy AES (from ZipAchieve) encrypted data
    ciphertext5 = "SLMBPbk5Ou8=" #from NGSystem.FrontServerController. Expects "netbrain".
    deciphertext5 = NBCrypto.decrypt_zip_aes(ciphertext5)
    print("AES ZipArchieve: expects=> {}, decipher result=> {}".format("netbrain", deciphertext5))

    #test legacy AES (from ZipAchieve) encryption
    #ciphertext5 = "SLMBPbk5Ou8=" #from NGSystem.FrontServerController. Expects "netbrain".
    plaintext5 = "netbrain"
    encrypted5 = NBCrypto.encrypt_zip_aes(plaintext5)
    print("AES ZipArchieve encrypt: plaintext=> {}, ciphertext=> {}, expects=> SLMBPbk5Ou8=".format(plaintext5, encrypted5))

    #test decrypt legacy .net Password Based Encryption (AES + PBKDF1) encrypted data
    ciphertext4 = "Ws0i7COgUfBEfG/4//OX3hv72A6SvKlqXohrlQK12Jg=" #from NGSystem.EmailSetting. Expects "yuhe.chen" in utf16 unicode format.
    password = "MOC.HCETNIARBTEN@OAIX.FFEJ"
    deciphertext4 = NBCrypto.decrypt_legacy_pbe(ciphertext4, password)
    print("AES PBKDF1: expects=> {}, decipher result=> {}".format("yuhe.chen", deciphertext4))

    #test AES 256 encrypt/decrypt using crypto key from keystore
    plaintext7 = "netbrain"
    ciphertext7 = NBCrypto.encrypt_aes_ks(plaintext7)
    deciphertext7 = NBCrypto.decrypt_aes_ks(ciphertext7)
    print("AES KE: ciphertext=> {}, decipher result=> {}".format(ciphertext7, deciphertext7))

    #test unicode
    unicode_txt = u'ユニコードエンコーディング'
    cipher = NBCrypto.encrypt_aes_ks(unicode_txt)
    print(cipher)
    decipher = NBCrypto.decrypt_aes_ks(cipher)
    print(decipher)

    hash_input = "sample input data"
    hashval = NBCrypto.spooky_hash(hash_input)
    print("Spooky hash: {}".format(hashval))

    # ciphertextplain = "mansfield=" #unencrypted EnableUsername from IE 7.0a. will cause exception
    # nonascii = NBCrypto.decrypt_zip_aes(ciphertextplain)
    # print("Decrypted non-ASCII: {}, isascii={}".format(nonascii, nonascii.isascii()))
    # print("Decrypted ASCII: {}, isascii={}".format(ciphertextplain, ciphertextplain.isascii()))



