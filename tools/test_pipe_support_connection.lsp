;;; =========================================================================
;;; AutoLISP: Prueba Directa de Tuberias ASME y Soportes U-Bolt (SIN VALVULAS)
;;; Valida el acople geometrico de UBOLT_STANDARD sobre tubos 2", 4" y 8".
;;; Ejecutar en AutoCAD Plant 3D pegando en la barra de comandos:
;;; (load "c:/Users/ynoacamino/dev/plant3d/tools/test_pipe_support_connection.lsp")
;;; =========================================================================

(defun c:TESTPIPESUPPORT ( / oldEcho acadApp doc ms DibujaTubo)
  (vl-load-com)
  (setq oldEcho (getvar "CMDECHO"))
  (setvar "CMDECHO" 0)
  
  (setq acadApp (vlax-get-acad-object))
  (setq doc (vla-get-ActiveDocument acadApp))
  (setq ms (vla-get-ModelSpace doc))

  ;; Funcion auxiliar para modelar un tramo de tubo cilindrico solido en el eje X
  (defun DibujaTubo (x y z radio long / pt cyl)
    (setq pt (vlax-3d-point x y (- z (/ long 2.0))))
    (setq cyl (vla-AddCylinder ms pt radio long))
    ;; Rotar 90 grados alrededor del eje Y para que quede paralelo al eje X
    (vla-Rotate3D cyl 
                  (vlax-3d-point x y z) 
                  (vlax-3d-point x (+ y 1.0) z) 
                  (/ pi 2.0))
    (vla-put-Color cyl 8) ; Color gris de tuberia
    cyl
  )

  (princ "\n[+] Cargando adaptador PnP3dACPAdapter...")
  (arxload "PnP3dACPAdapter")
  
  (princ "\n[+] Registrando scripts de CustomScripts...")
  (vl-cmdf "PLANTREGISTERCUSTOMSCRIPTS")

  ;; ------------------------------------------------------------------------
  ;; TRAMO 1: Tuberia 2" ASME B36.10 (OD = 2.375") + Abrazadera U 2"
  ;; ------------------------------------------------------------------------
  (princ "\n[+] Tramo 1 (2\"): Modelando tubo OD 2.375\" + Abrazadera U-Bolt 2\"...")
  (DibujaTubo 0.0 0.0 0.0 (/ 2.375 2.0) 24.0)
  
  (testacpscript "UBOLT_STANDARD"
    "OD" "2.375000" "A" "0.375000" "B" "2.519700"
    "C" "2.874000" "D" "3.385800" "E" "2.244100" "F" "2.204700")
  (vl-cmdf "_.change" (entlast) "" "_p" "_c" "2" "") ; Amarillo soporte 2"

  ;; ------------------------------------------------------------------------
  ;; TRAMO 2: Tuberia 4" ASME B36.10 (OD = 4.500") + Abrazadera U 4"
  ;; ------------------------------------------------------------------------
  (princ "\n[+] Tramo 2 (4\"): Modelando tubo OD 4.500\" + Abrazadera U-Bolt 4\"...")
  (DibujaTubo 0.0 20.0 0.0 (/ 4.500 2.0) 28.0)
  
  (testacpscript "UBOLT_STANDARD"
    "OD" "4.500000" "A" "0.500000" "B" "4.645700"
    "C" "5.157500" "D" "4.488200" "E" "2.992100" "F" "2.244100")
  (vl-cmdf "_.move" (entlast) "" '(0 0 0) '(0 20 0))
  (vl-cmdf "_.change" (entlast) "" "_p" "_c" "4" "") ; Cian soporte 4"

  ;; ------------------------------------------------------------------------
  ;; TRAMO 3: Tuberia 8" ASME B36.10 (OD = 8.625") + Abrazadera U 8"
  ;; ------------------------------------------------------------------------
  (princ "\n[+] Tramo 3 (8\"): Modelando tubo OD 8.625\" + Abrazadera U-Bolt 8\"...")
  (DibujaTubo 0.0 50.0 0.0 (/ 8.625 2.0) 36.0)
  
  (testacpscript "UBOLT_STANDARD"
    "OD" "8.625000" "A" "0.625000" "B" "8.818900"
    "C" "9.448800" "D" "7.086600" "E" "3.740200" "F" "2.755900")
  (vl-cmdf "_.move" (entlast) "" '(0 0 0) '(0 50 0))
  (vl-cmdf "_.change" (entlast) "" "_p" "_c" "3" "") ; Verde soporte 8"

  ;; ------------------------------------------------------------------------
  ;; Ajuste de camara a Isométrico Conceptual
  ;; ------------------------------------------------------------------------
  (princ "\n[+] Ajustando camara y estilo visual 3D...")
  (command "_.zoom" "_e")
  (command "_.vscurrent" "_c")
  (command "_.-view" "_swiso")
  (command "_.zoom" "_e")
  
  (setvar "CMDECHO" oldEcho)
  (princ "\n=========================================================================")
  (princ "\n[OK] Modelado completado exitosamente (SOLO TUBERIAS + SOPORTES):")
  (princ "\n     - Tramo 1: Tubo 2\" (OD 2.375\") + Abrazadera U Amarilla")
  (princ "\n     - Tramo 2: Tubo 4\" (OD 4.500\") + Abrazadera U Cian")
  (princ "\n     - Tramo 3: Tubo 8\" (OD 8.625\") + Abrazadera U Verde")
  (princ "\n=========================================================================\n")
  (princ)
)

;; Ejecutar automaticamente al cargar
(c:TESTPIPESUPPORT)
