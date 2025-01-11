from ocr.solver import CaptchaSolver

for i in range(10):
  try:
    solver = CaptchaSolver(f"ocr/testimages/captcha{i+1}.png")
    result = solver.solve_captcha()
    print(f"{i+1} result: {result}")
  except TypeError:
    print(f"{i+1} Hata")
    continue