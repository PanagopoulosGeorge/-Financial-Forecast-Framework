import concurrent.futures


def increment(value):
    return value + 1


values = [1, 2, 3, 4, 5, 3, 8, 2, 1]

# Add code here
if __name__ == "__main__":
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = [executor.submit(increment, value) for value in values]
    results = [future.result() for future in futures]
    print(results)
