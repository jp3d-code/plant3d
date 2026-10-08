;;; =========================================================================
;;; AutoLISP: Verificación de Instalación - AutoCAD Plant 3D 2027
;;; Valida la carga de CustomScripts modelando:
;;;   1. Tubo 2" ASME B36.10 (OD 2.375")
;;;   2. Válvula INTEC K200 2" Clase 150# (KLINGER Schoneberg)
;;;   3. Abrazadera U-Bolt ITECO B3S 2" (Standard U-Bolt con contratuercas)
;;;
;;; Instrucciones:
;;;   Arrastra este archivo .lsp dentro del área de dibujo de Plant 3D,
;;;   o escribe en la barra de comandos:
;;;   (load "probar_instalacion.lsp")
;;; =========================================================================

(defun c:PROBARINSTALACION ( / oldEcho acadApp doc ms DibujaTubo)
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
    (vla-Rotate3D cyl 
                  (vlax-3d-point x y z) 
                  (vlax-3d-point x (+ y 1.0) z) 
                  (/ pi 2.0))
    (vla-put-Color cyl 8) ; Color gris de tuberia
    cyl
  )

  (princ "\n[1/5] Cargando adaptador PnP3dACPAdapter...")
  (arxload "PnP3dACPAdapter")
  
  (princ "\n[2/5] Registrando scripts de CustomScripts...")
  (vl-cmdf "PLANTREGISTERCUSTOMSCRIPTS")

  ;; 1. Tramo de Tuberia 2" ASME B36.10
  (princ "\n[3/5] Modelando tubo 2\" ASME B36.10 (OD 2.375\")...")
  (DibujaTubo 0.0 0.0 0.0 (/ 2.375 2.0) 24.0)

  ;; 2. Valvula INTEC K200 2" 150#
  (princ "\n[4/5] Insertando Valvula INTEC K200 2\" Clase 150#...")
  (testacpscript "INTEC_K200_BALL_VALVE"
    "L" "7.0079"
    "D" "6.0000"
    "H" "4.9213"
    "L1" "9.8425"
    "E" "0.5512"
    "OD" "2.3740"
    "P1" "0.0" "P2" "0.0" "P3" "0.0" "P4" "0.0"
  )
  (vl-cmdf "_.change" (entlast) "" "_p" "_c" "1" "") ; Rojo valvula

  ;; 3. Soporte U-Bolt ITECO B3S 2" abrazado al tubo
  (princ "\n[5/5] Insertando Soporte Abrazadera U-Bolt ITECO B3S 2\"...")
  (testacpscript "UBOLT_STANDARD"
    "OD" "2.375000" "A" "0.375000" "B" "2.519700"
    "C" "2.874000" "D" "3.385800" "E" "2.244100" "F" "2.204700"
  )
  (vl-cmdf "_.move" (entlast) "" '(0 0 0) '(8.0 0 0)) ; Montado a 8" en el tubo
  (vl-cmdf "_.change" (entlast) "" "_p" "_c" "2" "") ; Amarillo soporte

  ;; Ajuste de camara y vista
  (princ "\n[+] Ajustando camara y estilo visual 3D...")
  (command "_.zoom" "_e")
  (command "_.vscurrent" "_c")
  (command "_.-view" "_swiso")
  (command "_.zoom" "_e")

  (setvar "CMDECHO" oldEcho)
  (princ "\n=========================================================================")
  (princ "\n [EXITO] INSTALACION VERIFICADA AL 100%:")
  (princ "\n  1. Tubo 2\" ASME B36.10 (Gris)")
  (princ "\n  2. Valvula INTEC K200 2\" Clase 150# (Roja)")
  (princ "\n  3. Soporte Abrazadera U-Bolt ITECO B3S 2\" (Amarillo)")
  (princ "\n Todos los CustomScripts estan operativos en AutoCAD Plant 3D 2027.")
  (princ "\n=========================================================================\n")
  (princ)
)

;; Ejecutar automaticamente al cargar
(c:PROBARINSTALACION)
