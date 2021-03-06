from argparse import ArgumentParser

from dls_python3_template_module import HelloClass, say_hello_lots


def main(args=None):
    parser = ArgumentParser()
    parser.add_argument("name", help="Name of the person to greet")
    parser.add_argument("--times", type=int, default=5, help="Number of times to greet")
    args = parser.parse_args(args)
    say_hello_lots(HelloClass(args.name), args.times)


if __name__ == "__main__":
    # test with:
    #     pipenv run python -m dls_python3_template_module.cli
    main()
