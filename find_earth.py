import cv2
import numpy as np
import os

def find_earth():
    # Caminho da imagem (robusto, independente de onde o script é executado)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(script_dir, "Aula3_cont_aula4", "images", "Pale_Blue_Dot.png")
    
    # Verifica se a imagem existe
    if not os.path.exists(image_path):
        print(f"Erro: Imagem não encontrada em {image_path}")
        return

    # Carrega a imagem
    img = cv2.imread(image_path)
    if img is None:
        print("Erro: Falha ao carregar a imagem.")
        return

    # Converte para HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Definição dos planetas e suas cores (Range HSV)
    # Earth: Blue
    earth_lower = np.array([90, 30, 100])
    earth_upper = np.array([140, 255, 255])

    # Mars: Red (precisa de dois ranges pois o vermelho dá a volta no círculo de matiz)
    mars_lower1 = np.array([0, 100, 100])
    mars_upper1 = np.array([10, 255, 255])
    mars_lower2 = np.array([170, 100, 100])
    mars_upper2 = np.array([180, 255, 255])

    planets = [
        {"name": "Terra", "color": (255, 0, 0), "masks": [(earth_lower, earth_upper)]},  # BGR para Blue é (255,0,0)? Não, BGR é Blue-Green-Red. Azul é (255,0,0)
        {"name": "Marte", "color": (0, 0, 255), "masks": [(mars_lower1, mars_upper1), (mars_lower2, mars_upper2)]} # Vermelho é (0,0,255)
    ]
    
    # Lista para guardar os dados
    results = []

    for planet in planets:
        # Cria a máscara combinada
        final_mask = np.zeros(hsv.shape[:2], dtype="uint8")
        for (lower, upper) in planet["masks"]:
            mask = cv2.inRange(hsv, lower, upper)
            final_mask = cv2.bitwise_or(final_mask, mask)

        # Encontra contornos
        contours, _ = cv2.findContours(final_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            # Pega o maior contorno
            largest_contour = max(contours, key=cv2.contourArea)
            
            # Encontra o centro e raio
            ((x, y), radius) = cv2.minEnclosingCircle(largest_contour)

            # Desenha
            color_bgr = planet["color"]
            cv2.circle(img, (int(x), int(y)), int(radius + 10), color_bgr, 2)
            cv2.putText(img, planet["name"], (int(x) + 15, int(y) - 15), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_bgr, 2)

            print(f"{planet['name']} detectado em: X={int(x)}, Y={int(y)}")
            results.append({'Objeto': planet['name'], 'X': int(x), 'Y': int(y)})
        else:
            print(f"{planet['name']} não detectado.")

    # Calcular distância Euclidiana se ambos forem detectados
    if len(results) >= 2:
        p1 = results[0] # Terra (assumindo ordem da lista)
        p2 = results[1] # Marte
        
        # Garante que estamos pegando os objetos certos pelo nome se a ordem mudar
        earth_data = next((item for item in results if item["Objeto"] == "Terra"), None)
        mars_data = next((item for item in results if item["Objeto"] == "Marte"), None)

        if earth_data and mars_data:
            # Refatorado para usar NumPy arrays conforme solicitado
            terra = np.array([earth_data['X'], earth_data['Y']])
            marte = np.array([mars_data['X'], mars_data['Y']])

            # Cálculo da distância Euclidiana usando NumPy
            # dist = sqrt((x2-x1)^2 + (y2-y1)^2)
            dist = np.linalg.norm(terra - marte)
            
            # Alternativa manual se fosse estritamente np.sqrt(sum((t-m)**2))
            # dist = np.sqrt(np.sum((terra - marte)**2))

            print(f"Distância Euclidiana entre Terra e Marte: {dist:.2f} pixels")

            # Desenha linha entre eles
            pt_earth = (int(terra[0]), int(terra[1]))
            pt_mars = (int(marte[0]), int(marte[1]))
            cv2.line(img, pt_earth, pt_mars, (255, 255, 255), 1)
            
            # Ponto médio para o texto
            mid_point = (terra + marte) / 2
            mid_x = int(mid_point[0])
            mid_y = int(mid_point[1])
            
            cv2.putText(img, f"{dist:.1f} px", (mid_x, mid_y - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Adiciona a distância aos resultados
            results.append({'Objeto': 'Distancia_Terra_Marte', 'X': np.nan, 'Y': np.nan, 'Distancia': dist})

    # Salva o resultado visual
    output_path = "planets_found.png"
    cv2.imwrite(output_path, img)
    print(f"Imagem com detecções salva em: {output_path}")

    # Salva os dados se houver resultados
    if results:
        try:
            import pandas as pd
            df = pd.DataFrame(results)

            # Salvar CSV
            csv_path = os.path.join(script_dir, "planets_coordinates.csv")
            df.to_csv(csv_path, index=False)
            print(f"Coordenadas salvas em CSV: {csv_path}")

            # Salvar XLSX
            xlsx_path = os.path.join(script_dir, "planets_coordinates.xlsx")
            df.to_excel(xlsx_path, index=False)
            print(f"Coordenadas salvas em XLSX: {xlsx_path}")
            
        except ImportError:
            print("Erro: Pandas ou openpyxl não instalados.")
        except Exception as e:
            print(f"Erro ao salvar dados: {e}")
            
if __name__ == "__main__":
    find_earth()
