from NetBrainIE import NetBrainIE

url = 'https://192.168.31.200/'
plainPassword = 'Admin@233'

def EncryptPassword():
    app = NetBrainIE(url)
    encrpytPassword = app.PasswordEncrypt(plainPassword)
    print(encrpytPassword)
    return encrpytPassword


if __name__ == '__main__':
    EncryptPassword()