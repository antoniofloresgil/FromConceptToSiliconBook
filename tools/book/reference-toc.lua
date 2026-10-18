-- Keep the four consultation chapters in the printed contents without adding
-- hundreds of glossary/matrix subentries. HTML retains the local heading TOCs.
function Header(header)
  if FORMAT:match("latex") and header.classes:includes("reference-entry") then
    header.classes:insert("unlisted")
    return header
  end
end
