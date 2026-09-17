def gerar_pdf(page, caminho):
    page.pdf(path=str(caminho), landscape=True, scale=1.0, print_background=True)
