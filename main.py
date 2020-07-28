import pdfplumber


def main():
    with pdfplumber.open('algebra-linear.pdf') as pdf:
        first_page = pdf.pages[0]
        im = first_page.to_image()


if __name__ == '__main__':
    main()
