;;; =========================================================================
;;; AutoLISP: Prueba de Soporte UBOLT_STANDARD 2" Nominal (OD = 2.375")
;;; Con vector de puerto corregido (0, 0, 1) alineado al eje del tubo.
;;; =========================================================================

(defun c:TEST2IN ()
  (vl-load-com)
  (princ "\n[+] Recargando PnP3dACPAdapter y registrando scripts...")
  (arxload "PnP3dACPAdapter")
  (vl-cmdf "PLANTREGISTERCUSTOMSCRIPTS")

  (princ "\n[+] Instanciando UBOLT_STANDARD para Tubo de 2\" (OD=2.375\")...")
  ;; Parametros exactos del catalogo para 2"
  (testacpscript "UBOLT_STANDARD"
    "OD" "2.375000"
    "A"  "0.375000"
    "B"  "2.519700"
    "C"  "2.874000"
    "D"  "3.385800"
    "E"  "2.244100"
    "F"  "2.204700"
  )

  (princ "\n[+] Ajustando camara...")
  (command "_.zoom" "_e")
  (command "_.vscurrent" "_c")
  (command "_.-view" "_swiso")
  (command "_.zoom" "_e")
  (princ "\n[OK] Abrazadera de 2\" instanciada correctamente!\n")
  (princ)
)

(c:TEST2IN)
