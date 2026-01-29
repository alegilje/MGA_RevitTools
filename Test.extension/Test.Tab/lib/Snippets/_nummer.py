# Encoding: utf-8


def sjekke_avvik(liste1,liste2):
    if liste1 != liste2:
        avvik = []
        if liste1 > liste2:
            avvik = liste1 - liste2
        else:
            avvik = liste2 - liste1
    else:
        avvik = 0
    return avvik