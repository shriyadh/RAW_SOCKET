# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import socket
def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("david.choffnes.com", 80))
        print(socket.gethostbyname("david.choffnes.com"))
        ip, port = sock.getsockname()
        print("))IP*****************************************", ip)

        print(socket.gethostbyname(socket.gethostname()))
    except Exception as err:
        raise err
    finally:
        sock.close()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
