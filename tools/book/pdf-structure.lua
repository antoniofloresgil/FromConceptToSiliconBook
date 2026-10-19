-- Keep the source/HTML chapter order while placing PDF contents after Preface.
function Header(header)
  if FORMAT:match("latex") and header.level == 1 and header.identifier == "introduction" then
    return {pandoc.RawBlock("latex", "\\BookContents\n\\BookMainMatter"), header}
  end
end

-- Percentage-width diagrams must leave room for their heading and caption.
-- Both dimensions are constraints, so smaller/wider figures retain their width.
function Image(image)
  if FORMAT:match("latex") and not image.attributes.height
    and (image.attributes.width or ""):match("%%$") then
    image.attributes.height = "85%"
    return image
  end
end
