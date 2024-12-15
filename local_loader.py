import json
import os


class JSONLoader:
    def __init__(self, file_path):
        """
        Инициализирует экземпляр класса и загружает данные из JSON-файла.

        :param file_path: Путь к JSON-файлу.
        """
        self.data = {}
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Файл {file_path} не найден.")

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                self.data = json.load(file)
        except json.JSONDecodeError as e:
            raise ValueError(f"Ошибка при разборе JSON-файла: {e}")

    def get_value(self, key):
        """
        Возвращает значение по заданному ключу из загруженных данных.

        :param key: Ключ для поиска значения.
        :return: Значение, связанное с ключом, или None, если ключ не найден.
        """
        return self.data.get(key)