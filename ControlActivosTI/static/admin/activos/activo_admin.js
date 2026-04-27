(function () {
  function tipoSeleccionadoUsaEspecificaciones(select) {
    if (!select || select.selectedIndex < 0) {
      return false;
    }

    var texto = select.options[select.selectedIndex].text.toLowerCase();
    return ["laptop", "pc", "desktop", "escritorio", "computador", "computadora"].some(function (clave) {
      return texto.indexOf(clave) !== -1;
    });
  }

  function actualizarCamposTecnicos() {
    var selectTipo = document.getElementById("id_tipo_activo");
    var mostrar = tipoSeleccionadoUsaEspecificaciones(selectTipo);
    var campos = ["cpu", "ram", "disco", "sistema_operativo"];

    campos.forEach(function (campo) {
      var fila = document.querySelector(".form-row.field-" + campo);
      var input = document.getElementById("id_" + campo);

      if (fila) {
        fila.style.display = mostrar ? "" : "none";
      }

      if (input && !mostrar) {
        input.value = "";
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var selectTipo = document.getElementById("id_tipo_activo");
    actualizarCamposTecnicos();

    if (selectTipo) {
      selectTipo.addEventListener("change", actualizarCamposTecnicos);
    }
  });
})();
