-- HTML keeps explicit Roman prefixes; LaTeX numbers book parts itself.
local function strip_prefix(title, position)
  local first = title.content[position]
  if first and first.t == "Str" and first.text:match("^[IVXLCDM]+%.$") then
    title.content:remove(position)
    if title.content[position] and title.content[position].t == "Space" then
      title.content:remove(position)
    end
    return title
  end
end

function Div(div)
  if not FORMAT:match("latex") or not div.classes:includes("quarto-book-part") then
    return nil
  end
  return div:walk({
    Header = function(header)
      if header.level == 1 then
        return strip_prefix(header, 1)
      end
    end,
    Para = function(para)
      local first = para.content[1]
      -- Quarto may already have converted the part heading to a LaTeX command.
      if first and first.t == "RawInline" and first.format == "latex"
        and first.text == "\\part{" then
        return strip_prefix(para, 2)
      end
    end
  })
end
