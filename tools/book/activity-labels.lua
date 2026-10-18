-- Keep a standalone activity label with the first line of its instructions.
-- Otherwise the short label can satisfy LaTeX's heading keep rule by itself.
function Para(para)
  if not FORMAT:match("latex") or #para.content ~= 1 then
    return nil
  end
  local link = para.content[1]
  if link.t == "Span" and link.classes:includes("reference-destination") then
    return {para, pandoc.RawBlock("latex", "\\nopagebreak[4]")}
  end
  if link.t == "Link" and link.classes:includes("learning-activity") then
    return {para, pandoc.RawBlock("latex", "\\nopagebreak[4]")}
  end
end
