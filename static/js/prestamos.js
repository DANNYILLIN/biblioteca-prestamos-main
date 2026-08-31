// Variables globales para almacenar lo que vamos encontrando
let datosPrestamo = {
    usuario: null,
    libro: null,
    esManual: false
};

// 1. ESCUCHAR EL ESCÁNER DE DNI / CÓDIGO DE MATRÍCULA
document.getElementById('input-dni').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        const codigo = this.value.trim();
        if (codigo) buscarUsuario(codigo);
    }
});

// 2. ESCUCHAR EL ESCÁNER DEL LIBRO
document.getElementById('input-libro').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        const codigoBarras = this.value.trim();
        if (codigoBarras) buscarLibro(codigoBarras);
    }
});

// --- FUNCIONES DE BÚSQUEDA ---

async function buscarUsuario(codigo) {
    try {
        const response = await fetch('/api/buscar_usuario', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ codigo: codigo })
        });
        const data = await response.json();

        if (data.success) {
            datosPrestamo.usuario = data.usuario;
            datosPrestamo.esManual = false;
            mostrarUsuarioEnPantalla(data.usuario);
        } else {
            const quiereRegistrar = confirm("El DNI/Matrícula no está registrado. ¿Desea ingresar los datos manualmente?");
            if (quiereRegistrar) {
                datosPrestamo.esManual = true;
                document.getElementById('nombre-lector').innerHTML = `
                    <input type="text" id="manual-nombre" 
                           class="w-full p-2 border-2 border-amber-400 rounded text-sm text-black uppercase" 
                           placeholder="ESCRIBA NOMBRE COMPLETO">
                `;
                document.getElementById('info-lector').innerHTML = `
                    <div class="grid grid-cols-2 gap-2 mt-2">
                        <input type="text" id="manual-dni" value="${codigo}" class="p-2 border rounded text-xs text-black" placeholder="DNI">
                        <input type="text" id="manual-escuela" class="p-2 border rounded text-xs text-black" placeholder="FACULTAD / ESCUELA">
                    </div>
                `;
                document.getElementById('manual-nombre').focus();
            }
        }
    } catch (err) {
        console.error("Error en búsqueda:", err);
    }
}

async function buscarLibro(codigoBarras) {
    try {
        const response = await fetch('/api/buscar_libro', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ codigo_barras: codigoBarras })
        });
        const data = await response.json();

        if (data.success) {
            datosPrestamo.libro = data.libro;
            mostrarLibroEnPantalla(data.libro);
        } else {
            alert("El libro no existe en el catálogo o no está disponible.");
        }
    } catch (err) {
        console.error("Error:", err);
    }
}

// --- INTERFAZ DE USUARIO ---

function mostrarUsuarioEnPantalla(u) {
    // 1. Ponemos el nombre en grande
    document.getElementById('nombre-lector').textContent = u.nombre;
    
    // 2. Creamos la interfaz de info + el campo de celular
    document.getElementById('info-lector').innerHTML = `
        <div class="flex flex-col space-y-3 mt-2">
            <div class="flex items-center space-x-2 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                <span class="bg-slate-100 px-2 py-1 rounded">${u.tipo}</span>
                <span>•</span>
                <span>DNI: ${u.dni}</span>
            </div>

            <div class="relative group">
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <i class="fas fa-mobile-alt text-amber-500 transition-colors group-focus-within:text-amber-600"></i>
                </div>
                <input type="number" id="input-celular" 
                    class="w-full pl-9 pr-4 py-3 bg-amber-50 border-2 border-amber-100 rounded-xl text-sm font-black text-slate-700 outline-none focus:border-amber-400 focus:ring-4 focus:ring-amber-500/5 transition-all placeholder:font-medium placeholder:text-slate-400" 
                    placeholder="INGRESAR CELULAR (9 DÍGITOS)"
                    oninput="if(this.value.length > 9) this.value = this.value.slice(0, 9);">
            </div>
        </div>
    `;

    // 3. Auto-enfocar el campo de celular para ganar velocidad
    setTimeout(() => {
        document.getElementById('input-celular').focus();
    }, 100);
}

function mostrarLibroEnPantalla(l) {
    document.getElementById('titulo-libro').textContent = l.Titulo;
    document.getElementById('autor-libro').textContent = l.Autor || "Autor no registrado";
    
    // Escapamos comillas por si el título o autor tienen apóstrofes (ej: O'Reilly)
    const tituloLimpio = l.Titulo.replace(/'/g, "\\'");
    const autorLimpio = (l.Autor || "").replace(/'/g, "\\'");

    document.getElementById('detalles-libro').innerHTML = `
        <div class="bg-slate-100 p-2 rounded">
            <span class="block text-[10px] text-slate-400 font-bold">CONOC.</span>
            <span class="font-bold text-slate-700">${l.CodigoConocimiento || '---'}</span>
        </div>
        <div class="bg-slate-100 p-2 rounded">
            <span class="block text-[10px] text-slate-400 font-bold">NOT. INT.</span>
            <span class="font-bold text-slate-700">${l.NotacionInterna || '---'}</span>
        </div>
        <div class="bg-slate-100 p-2 rounded">
            <span class="block text-[10px] text-slate-400 font-bold">SECUENC.</span>
            <span class="font-bold text-slate-700">${l.Secuenc || '---'}</span>
        </div>
        <div class="bg-slate-100 p-2 rounded">
            <span class="block text-[10px] text-slate-400 font-bold">LOCAL</span>
            <span class="font-bold text-slate-700">${l.Local || '---'}</span>
        </div>
        
        <!-- BOTÓN DE INTELIGENCIA ARTIFICIAL -->
        <div class="col-span-2 mt-2">
            <button onclick="generarResenaIA('${tituloLimpio}', '${autorLimpio}')" 
                    class="w-full bg-indigo-50 hover:bg-indigo-100 text-indigo-600 border border-indigo-200 p-2.5 rounded-xl text-[11px] font-black uppercase tracking-wider flex items-center justify-center gap-2 transition-all shadow-sm">
                <i class="fas fa-robot text-sm"></i>
                Consultar Reseña con IA
            </button>
        </div>
    `;
}

// --- PROCESO DE IMPRESIÓN Y GUARDADO ---

async function confirmarPrestamo() {
    // 1. Capturar el celular (siempre presente si se buscó o registró alguien)
    const inputCel = document.getElementById('input-celular');
    const manualCel = document.getElementById('manual-celular'); // Por si lo pones en el form manual
    
    // Prioridad al input de celular que creamos en mostrarUsuarioEnPantalla
    const valorCelular = (inputCel ? inputCel.value.trim() : (manualCel ? manualCel.value.trim() : ""));

    // Validación: No permitir préstamos sin celular
    if (!valorCelular || valorCelular.length < 9) {
        alert("⚠️ Por favor, ingrese un número de celular válido para contactar al lector.");
        if(inputCel) inputCel.focus();
        return;
    }

    // 2. Manejo de Registro Manual
    if (datosPrestamo.esManual) {
        const nombreManual = document.getElementById('manual-nombre').value.trim();
        const dniManual = document.getElementById('manual-dni').value.trim();

        if (!nombreManual) {
            alert("Ingrese el nombre del lector.");
            return;
        }

        datosPrestamo.usuario = {
            nombre: nombreManual,
            dni: dniManual,
            tipo: "REGISTRO MANUAL",
            celular: valorCelular // Agregamos el celular aquí
        };
    } else {
        // Si no es manual, agregamos el celular al objeto de usuario ya encontrado
        if (datosPrestamo.usuario) {
            datosPrestamo.usuario.celular = valorCelular;
        }
    }

    // 3. Verificación final de datos
    if (!datosPrestamo.usuario || !datosPrestamo.libro) {
        alert("Faltan datos del usuario o del libro.");
        return;
    }

    try {
        // ENVIAR A LA BASE DE DATOS (Incluye el celular dentro de datosPrestamo.usuario)
        const response = await fetch('/api/confirmar_prestamo', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(datosPrestamo)
        });
        
        const res = await response.json();

        if (res.success) {
            const sala = document.getElementById('input-sala').value || "Biblioteca Central";
            const ticketHtml = generarHtmlVoucher(datosPrestamo, sala);
            document.getElementById('seccion-impresion').innerHTML = ticketHtml;
            
            window.print();
            
            alert("✅ Préstamo registrado y ticket generado.");
            location.reload(); 
        } else {
            alert("❌ Error al guardar en base de datos: " + res.message);
        }
    } catch (err) {
        console.error("Error confirmando préstamo:", err);
        alert("No se pudo conectar con el servidor.");
    }
}

function generarHtmlVoucher(d, sala) {
    // Definimos el cuerpo del ticket (el contenido base)
    const contenidoTicket = `
        <div style="font-family: 'Courier New', Courier, monospace; font-size: 12px; color: black; line-height: 1.3; padding: 10px;">
            <div style="text-align: center; font-weight: bold; margin-bottom: 5px;">
                <span style="font-size: 14px;">UNIV. NACIONAL DANIEL ALCIDES CARRIÓN</span><br>
                <span>BIBLIOTECA CENTRAL - UNDAC</span><br>
                <span>--------------------------------</span><br>
                <span>TICKET DE PRÉSTAMO</span>
            </div>

            <div style="margin: 10px 0;">
                <p style="margin: 2px 0;"><strong>FECHA:</strong> ${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</p>
                <p style="margin: 2px 0;"><strong>SALA:</strong> ${sala.toUpperCase()}</p>
            </div>

            <div style="border-top: 1px dashed #000; border-bottom: 1px dashed #000; padding: 5px 0; margin: 10px 0;">
                <p style="margin: 2px 0;"><strong>LECTOR:</strong> ${d.usuario.nombre.toUpperCase()}</p>
                <p style="margin: 2px 0;"><strong>DNI:</strong> ${d.usuario.dni}</p>
                <p style="margin: 2px 0;"><strong>CELULAR:</strong> ${d.usuario.celular || 'S/N'}</p>
                <p style="margin: 2px 0;"><strong>TIPO:</strong> ${d.usuario.tipo}</p>
            </div>

            <div style="margin: 10px 0;">
                <p style="margin: 2px 0;"><strong>LIBRO:</strong> ${d.libro.Titulo.toUpperCase()}</p>
                <p style="margin: 2px 0;"><strong>AUTOR:</strong> ${d.libro.Autor || 'S/A'}</p>
                <p style="margin: 2px 0;"><strong>CÓDIGO:</strong> ${d.libro.Secuenc}</p>
            </div>

            <div style="margin-top: 20px; text-align: center;">
                <p>__________________________</p>
                <p style="font-size: 10px;">FIRMA DEL LECTOR</p>
            </div>
        </div>
    `;

    // Retornamos los dos tickets con una línea de corte clara
    return `
        <div class="ticket-container">
            <div style="border: 1px solid #ccc; margin-bottom: 10px; position: relative;">
                <span style="position: absolute; top: 5px; right: 10px; font-size: 9px; font-weight: bold; color: #666;">COPIA BIBLIOTECA</span>
                ${contenidoTicket}
            </div>

            <div style="text-align: center; margin: 15px 0; border-top: 2px dashed #444; position: relative;">
                <span style="position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: white; padding: 0 10px; font-size: 14px;">✂--------------------</span>
            </div>

            <div style="border: 1px solid #ccc; position: relative;">
                <span style="position: absolute; top: 5px; right: 10px; font-size: 9px; font-weight: bold; color: #666;">COPIA USUARIO</span>
                ${contenidoTicket}
            </div>
        </div>
    `;
}

async function generarResenaIA(titulo, autor) {
    // 1. Mostrar estado de carga
    Swal.fire({
        title: 'Consultando IA...',
        text: 'Generando reseña en tiempo real',
        allowOutsideClick: false,
        didOpen: () => Swal.showLoading()
    });

    try {
        // 2. Hacer la petición a tu nueva ruta en Flask
        const response = await fetch('/api/resena_ia', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ titulo: titulo, autor: autor })
        });
        const data = await response.json();

        // 3. Mostrar el resultado
        if (data.success) {
            Swal.fire({
                title: `Reseña: ${titulo}`,
                text: data.resena,
                icon: 'info',
                confirmButtonColor: '#10b981'
            });
        } else {
            Swal.fire('Error', data.error, 'error');
        }
    } catch (err) {
        Swal.fire('Error', 'No se pudo conectar con el servidor', 'error');
    }
}