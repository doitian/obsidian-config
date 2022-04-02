for FILE in .obsidian/bin/ob-*; do
  if [ -x "$FILE" ]; then
    case "$(basename "$FILE")" in
      ob-chore.sh)
        ;;
      *)
        echo "==> $FILE"
        "$FILE"
        ;;
    esac
  fi
done
