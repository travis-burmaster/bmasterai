import bmasterai
import logging

bmasterai.configure_logging()
logger = bmasterai.get_logger()

print("--- type(logger.logger) ---")
try:
    print(type(logger.logger))
except AttributeError:
    print("No logger.logger")

print("\n--- bmasterai.EventType ---")
try:
    for e in bmasterai.EventType:
        print(e)
except:
    print(dir(bmasterai.EventType))
