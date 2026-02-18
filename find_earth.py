import cv2
import numpy as np
import pandas as pd
import requests
from pathlib import Path
from typing import List, Dict, Optional, Tuple

def download_image(url: str, filepath: Path) -> bool:
    """
    Downloads an image from a URL to a filepath.
    Baixa uma imagem de uma URL para um caminho de arquivo.
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Image downloaded to / Imagem baixada para: {filepath}")
        return True
    except requests.RequestException as e:
        print(f"Error downloading image / Erro ao baixar imagem: {e}")
        return False

def find_earth() -> None:
    """
    Detects Earth in an image using HSV segmentation.
    Detecta a Terra em uma imagem usando segmentação HSV.
    """
    # Define paths using pathlib for robustness / Define caminhos usando pathlib para robustez
    script_dir = Path(__file__).parent.resolve()
    image_name = "pale_blue_dot.png"
    image_path = script_dir / image_name
    
    # URL provided by user / URL fornecida pelo usuário
    image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/Pale_Blue_Dot.png/330px-Pale_Blue_Dot.png"

    # Check if image exists / Verifica se a imagem existe
    if not image_path.exists():
        print(f"Image not found. Downloading from Wikipedia... / Imagem não encontrada. Baixando da Wikipedia...")
        if not download_image(image_url, image_path):
            return

    # Load image / Carrega a imagem
    img = cv2.imread(str(image_path))
    if img is None:
        print("Error: Failed to load image. / Erro: Falha ao carregar a imagem.")
        return

    # Convert to HSV / Converte para HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Define HSV ranges for Earth (Blue/Whitish-Blue) / Define faixas HSV para a Terra (Azul/Azul-esbranquiçado)
    # The Pale Blue Dot is very faint and small.
    # O Pálido Ponto Azul é muito tênue e pequeno.
    # Adjusting for a broader range of blue/cyan/white
    # Ajustando para uma faixa mais ampla de azul/ciano/branco
    
    # Broad range for whitish-blue
    # Faixa ampla para azul-esbranquiçado
    earth_lower = np.array([80, 5, 150]) # Lower saturation, reasonable value
    earth_upper = np.array([130, 255, 255]) # Upper limit

    planets: List[Dict] = [
        {"name_en": "Earth", "name_pt": "Terra", "color": (255, 0, 0), "masks": [(earth_lower, earth_upper)]},  # Blue in BGR / Azul em BGR
    ]
    
    results: List[Dict] = []

    for planet in planets:
        # Create combined mask / Cria máscara combinada
        final_mask = np.zeros(hsv.shape[:2], dtype="uint8")
        for (lower, upper) in planet["masks"]:
            mask = cv2.inRange(hsv, lower, upper)
            final_mask = cv2.bitwise_or(final_mask, mask)

        # Find contours / Encontra contornos
        contours, _ = cv2.findContours(final_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            # Get largest contour / Pega o maior contorno
            largest_contour = max(contours, key=cv2.contourArea)
            
            # Find center and radius / Encontra centro e raio
            ((x, y), radius) = cv2.minEnclosingCircle(largest_contour)

            # Draw / Desenha
            color_bgr = planet["color"]
            # Enforce a minimum radius for visibility / Força um raio mínimo para visibilidade
            draw_radius = max(int(radius + 5), 5)
            cv2.circle(img, (int(x), int(y)), draw_radius, color_bgr, 1)
            
            # Draw Arrow / Desenha Seta
            # Arrow tip at (x - draw_radius - 5, y) to point at the circle from the left
            # Ponta da seta em (x - draw_radius - 5, y) apontando para o círculo da esquerda
            start_point = (int(x) - 50, int(y))
            end_point = (int(x) - draw_radius - 2, int(y))
            cv2.arrowedLine(img, start_point, end_point, color_bgr, 2, tipLength=0.3)

            label = f"{planet['name_en']}/{planet['name_pt']}"
            cv2.putText(img, label, (int(x) - 60, int(y) - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, color_bgr, 1)

            print(f"{planet['name_en']} detected at / {planet['name_pt']} detectada em: X={int(x)}, Y={int(y)}")
            results.append({
                'Object/Objeto': label, 
                'X': int(x), 
                'Y': int(y)
            })
        else:
            print(f"{planet['name_en']} not detected. / {planet['name_pt']} não detectada.")

    # Save visual result / Salva resultado visual
    output_path = script_dir / "earth_highlighted.png"
    cv2.imwrite(str(output_path), img)
    print(f"Annotated image saved at / Imagem anotada salva em: {output_path}")

    # Save data if results exist / Salva dados se houver resultados
    if results:
        try:
            df = pd.DataFrame(results)

            # Save CSV / Salvar CSV
            csv_path = script_dir / "earth_coordinates.csv"
            df.to_csv(csv_path, index=False)
            print(f"Coordinates saved to CSV / Coordenadas salvas em CSV: {csv_path}")

            # Save XLSX / Salvar XLSX
            xlsx_path = script_dir / "earth_coordinates.xlsx"
            df.to_excel(xlsx_path, index=False)
            print(f"Coordinates saved to XLSX / Coordenadas salvas em XLSX: {xlsx_path}")
            
        except Exception as e:
            print(f"Error saving data / Erro ao salvar dados: {e}")
            
if __name__ == "__main__":
    find_earth()
