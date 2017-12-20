
(setq docs-dir "/Users/finngrimwood/git/demo-undo-code/xml/")
(setq docs-search-tool "/Users/finngrimwood/git/docs.el/doxygen_search.py")

(defun docs-at-point ()
  (interactive)
  (let* ((symbol (symbol-at-point))
         (command (format "python3 %s -x %s -s %s" docs-search-tool docs-dir symbol))
         (docs-text (replace-regexp-in-string "\n$" "" (shell-command-to-string command))))
    (popup-tip docs-text :around t :truncate nil :margin-right 1 )))
