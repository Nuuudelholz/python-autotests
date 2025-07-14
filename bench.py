import argparse
import re
import sys
import time
import requests

def parse_args():
    parser = argparse.ArgumentParser()

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-H', '--hosts', type=str, help='Список хостов без пробела, через запятую')
    group.add_argument('-F', '--file', type=str, help='Путь к файлу с хостами')

    parser.add_argument('-C', '--count', type=int, default=1, help='Число запросов для каждого хоста')
    parser.add_argument('-O', '--output', type=str, help='Вывод информации в файл (можно не прописывать)')
    return parser.parse_args()

def validate_host(url):
    return re.match(r'^https://[\w.-]+(?:\.[\w\.-]+)+$', url)

def get_hosts_from_args(args):
    if args.file:
        try:
            with open(args.file, 'r') as f:
                hosts = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f'Ошибка чтения файла: {e}')
            sys.exit(1)
    else:
        hosts = args.hosts.split(',')

    valid_hosts = []
    for host in hosts:
        if not validate_host(host):
            print(f'Неверный формат URL: {host}')
        else:
            valid_hosts.append(host)

    if not valid_hosts:
        print('Нет ни одного корректного хоста')
        sys.exit(1)

    return valid_hosts


def test_host(host, count):
    success, failed, errors = 0, 0, 0
    times = []

    for _ in range(count):
        try:
            start = time.time()
            response = requests.get(host)
            elapsed = time.time() - start

            if 200 <= response.status_code < 400:
                success += 1
            elif 400 <= response.status_code < 600:
                failed += 1

            times.append(elapsed)

        except requests.exceptions.RequestException:
            errors += 1

    return {
        'host': host,
        'success': success,
        'failed': failed,
        'errors': errors,
        'min': min(times) if times else 0,
        'max': max(times) if times else 0,
        'avg': sum(times)/len(times) if times else 0
    }

def format_stats(stats):
    return (
        f"\nHost: {stats['host']}\n"
        f"Success: {stats['success']}\n"
        f"Failed: {stats['failed']}\n"
        f"Errors: {stats['errors']}\n"
        f"Min: {stats['min']:.3f} s\n"
        f"Max: {stats['max']:.3f} s\n"
        f"Avg: {stats['avg']:.3f} s\n"
    )

def main():
    args = parse_args()

    if args.count <= 0:
        print('Количество запросов (-C) должно быть положительным числом!')
        sys.exit(1)

    hosts = get_hosts_from_args(args)
    results = []

    for host in hosts:
        result = test_host(host, args.count)
        results.append(result)

    output = '\n'.join(format_stats(r) for r in results)

    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f'Результат сохранён в {args.output}')
        except Exception as e:
            print(f'Ошибка записи в файл: {e}')
    else:
        print(output)

if __name__ == "__main__":
    main()