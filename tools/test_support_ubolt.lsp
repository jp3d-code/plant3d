(defun c:TESTUBOLT ()
  (vl-load-com)
  (princ "\n[+] Cargando PnP3dACPAdapter...")
  (arxload "PnP3dACPAdapter")
  
  (princ "\n[+] Registrando scripts de CustomScripts...")
  (vl-cmdf "PLANTREGISTERCUSTOMSCRIPTS")
  
  (princ "\n[+] Insertando geometria UBOLT_STANDARD...")
  (testacpscript "UBOLT_STANDARD")
  
  (princ "\n[+] Configurando vista 3D e iluminacion conceptual...")
  (command "_.zoom" "_e")
  (command "_.vscurrent" "_c")
  (command "_.-view" "_swiso")
  (command "_.zoom" "_e")
  (princ "\n[OK] Abrazadera UBOLT_STANDARD instanciada correctamente en (0,0,0)!\n")
  (princ)
)

(c:TESTUBOLT)
