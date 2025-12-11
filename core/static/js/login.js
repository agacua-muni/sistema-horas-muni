/* Archivo: core/static/js/login.js */
document.addEventListener("DOMContentLoaded", function() {
    // Buscamos el campo de contraseña
    var passwordInput = document.querySelector('input[name="password"]');
    
    if (passwordInput) {
        // Buscamos el contenedor padre (el input-group de Bootstrap)
        var inputGroup = passwordInput.closest('.input-group');
        
        if (inputGroup) {
            // Aseguramos que el contenedor tenga posición relativa para que el ícono flote dentro de él
            inputGroup.style.position = 'relative';

            // Creamos el icono del ojo
            var icon = document.createElement('i');
            icon.className = 'fas fa-eye';
            
            // ESTILOS CLAVE: Lo hacemos flotar sobre el input sin romper la estructura
            icon.style.position = 'absolute';
            icon.style.right = '50px'; // Lo separamos del borde derecho para no tapar el candado (aprox 40-50px)
            icon.style.top = '50%';
            icon.style.transform = 'translateY(-50%)'; // Centrado vertical perfecto
            icon.style.cursor = 'pointer';
            icon.style.color = '#6c757d'; // Color gris suave igual al del candado
            icon.style.zIndex = '100'; // Que quede por encima del texto

            // Función de click (mostrar/ocultar)
            icon.addEventListener('click', function() {
                if (passwordInput.type === "password") {
                    passwordInput.type = "text";
                    icon.className = 'fas fa-eye-slash';
                } else {
                    passwordInput.type = "password";
                    icon.className = 'fas fa-eye';
                }
            });

            // Agregamos el ícono al grupo
            inputGroup.appendChild(icon);
        }
    }
});