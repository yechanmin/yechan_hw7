from bootstrap.container import Container

def main():
    app = Container().build_app()
    app.launch()

if __name__ == "__main__":
    main()