-- Permit line breaks in long inline identifiers without changing their text.
-- Native Code nodes let Pandoc retain its own escaping of TeX special characters.
function Code(el)
  if not FORMAT:match("latex") or #el.text <= 24 or el.text:find("[^\032-\126]") then
    return nil
  end
  local result = pandoc.List()
  for offset = 1, #el.text, 16 do
    if offset > 1 then
      result:insert(pandoc.RawInline("latex", "\\allowbreak{}"))
    end
    local identifier = offset == 1 and el.identifier or ""
    result:insert(pandoc.Code(el.text:sub(offset, offset + 15),
      pandoc.Attr(identifier, el.classes, el.attributes)))
  end
  return result
end
