 if (
        localStorage.theme === "dark" ||
        (!("theme" in localStorage) &&
          window.matchMedia("(prefers-color-scheme: dark)").matches)
      ) {
        document.documentElement.classList.add("dark");
      } else {
        document.documentElement.classList.remove("dark");
      }

      // 2. The function our button will call to flip the switch
      function toggleDarkMode() {
        document.documentElement.classList.toggle("dark");
        if (document.documentElement.classList.contains("dark")) {
          localStorage.theme = "dark";
        } else {
          localStorage.theme = "light";
        }
      }