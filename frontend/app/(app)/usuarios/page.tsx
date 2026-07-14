"use client";

import { useState } from "react";

import {
  Button,
  Card,
  CargandoBloque,
  Chip,
  EstadoError,
  EstadoVacio,
  Etiqueta,
  Input,
  PageHeader,
  Select,
} from "@/components/ui";
import { useToast } from "@/components/toast";
import { ApiError } from "@/lib/api";
import { ROL_LABEL, tieneRol, useAuth } from "@/lib/auth";
import { useActualizarUsuario, useCrearUsuario, usePropiedades, useUsuarios } from "@/lib/hooks";

const ROLES = [
  "lector",
  "custodio_documental",
  "editor_propiedad",
  "editor_corporativo",
  "super_admin",
];
const NIVEL_LABEL: Record<number, string> = {
  1: "1 · Alta dirección",
  2: "2 · Dirección funcional",
  3: "3 · Jefatura / gerencia",
  4: "4 · Operativo",
};
const NIVEL_MAX_FIRMANTE = 3; // nivel_minimo_firmante (config); ≤3 ⇒ puede firmar

export default function UsuariosPage() {
  const { user } = useAuth();
  const { notify } = useToast();
  const { data, isLoading, isError, error } = useUsuarios();
  const { data: propiedades } = usePropiedades();
  const crear = useCrearUsuario();
  const actualizar = useActualizarUsuario();

  const propNombre = new Map((propiedades ?? []).map((p) => [p.id, p.codigo]));

  const [nombre, setNombre] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [nivel, setNivel] = useState(4);
  const [rol, setRol] = useState("lector");
  const [propiedad, setPropiedad] = useState(""); // "" = corporativo (todas)

  const [editId, setEditId] = useState<string | null>(null);
  const [eNivel, setENivel] = useState(4);
  const [eRol, setERol] = useState("lector");
  const [eActivo, setEActivo] = useState(true);
  const [ePropiedad, setEPropiedad] = useState("");

  function abrirEdicion(u: {
    id: string;
    nivel_jerarquico: number;
    activo: boolean;
    roles: { rol: string; propiedad_id: string | null }[];
  }) {
    setEditId(u.id);
    setENivel(u.nivel_jerarquico);
    setERol(u.roles[0]?.rol ?? "lector");
    setEPropiedad(u.roles[0]?.propiedad_id ?? "");
    setEActivo(u.activo);
  }

  async function guardarEdicion(id: string) {
    try {
      await actualizar.mutateAsync({
        id,
        body: {
          nivel_jerarquico: eNivel,
          activo: eActivo,
          roles: [{ rol: eRol, propiedad_id: ePropiedad || null }],
        },
      });
      notify("Usuario actualizado.");
      setEditId(null);
    } catch (err) {
      notify(err instanceof ApiError ? err.detail : "No se pudo actualizar.", "error");
    }
  }

  if (!tieneRol(user, "super_admin")) {
    return (
      <div>
        <PageHeader titulo="Usuarios" />
        <EstadoVacio titulo="Sin permisos" descripcion="Solo el super administrador gestiona usuarios." />
      </div>
    );
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!nombre.trim() || !email.trim() || password.length < 8)
      return notify("Nombre, correo y contraseña (mín. 8) son obligatorios.", "error");
    try {
      await crear.mutateAsync({
        nombre: nombre.trim(),
        email: email.trim(),
        password,
        nivel_jerarquico: nivel,
        roles: [{ rol, propiedad_id: propiedad || null }],
      });
      notify(`Usuario ${email.trim()} creado.`);
      setNombre("");
      setEmail("");
      setPassword("");
      setNivel(4);
      setRol("lector");
      setPropiedad("");
    } catch (err) {
      notify(err instanceof ApiError ? err.detail : "No se pudo crear el usuario.", "error");
    }
  }

  return (
    <div>
      <PageHeader
        titulo="Usuarios"
        descripcion="Padrón de usuarios: nivel jerárquico, rol y alcance. El alcance por propiedad define qué hotel ve cada usuario (corporativo = ve todos)."
      />

      <Card className="mb-6 p-6">
        <p className="mb-4 text-sm font-medium text-carbon">Nuevo usuario</p>
        <form onSubmit={onSubmit} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <Etiqueta htmlFor="n">Nombre *</Etiqueta>
            <Input id="n" value={nombre} onChange={(e) => setNombre(e.target.value)} />
          </div>
          <div>
            <Etiqueta htmlFor="e">Correo *</Etiqueta>
            <Input id="e" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div>
            <Etiqueta htmlFor="p">Contraseña * (mín. 8)</Etiqueta>
            <Input id="p" type="text" value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          <div>
            <Etiqueta htmlFor="niv">Nivel jerárquico</Etiqueta>
            <Select id="niv" value={nivel} onChange={(e) => setNivel(Number(e.target.value))}>
              {[1, 2, 3, 4].map((n) => (
                <option key={n} value={n}>
                  {NIVEL_LABEL[n]}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <Etiqueta htmlFor="rol">Rol</Etiqueta>
            <Select id="rol" value={rol} onChange={(e) => setRol(e.target.value)}>
              {ROLES.map((r) => (
                <option key={r} value={r}>
                  {ROL_LABEL[r] ?? r}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <Etiqueta htmlFor="prop">Alcance (propiedad)</Etiqueta>
            <Select id="prop" value={propiedad} onChange={(e) => setPropiedad(e.target.value)}>
              <option value="">— Corporativo (todas) —</option>
              {(propiedades ?? []).map((p) => (
                <option key={p.id} value={p.id}>
                  {p.codigo} — {p.nombre}
                </option>
              ))}
            </Select>
          </div>
          <div className="flex items-end">
            <Button type="submit" disabled={crear.isPending}>
              {crear.isPending ? "Creando…" : "Crear usuario"}
            </Button>
          </div>
        </form>
      </Card>

      {isLoading ? (
        <CargandoBloque />
      ) : isError ? (
        <EstadoError mensaje={(error as Error)?.message} />
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-linea bg-petrol-tint/40 text-left text-xs uppercase tracking-wide text-carbon-suave">
                  <th className="px-4 py-3 font-semibold">Nombre</th>
                  <th className="px-4 py-3 font-semibold">Correo</th>
                  <th className="px-4 py-3 font-semibold">Nivel</th>
                  <th className="px-4 py-3 font-semibold">Roles</th>
                  <th className="px-4 py-3 font-semibold">Alcance</th>
                  <th className="px-4 py-3 font-semibold">Estado</th>
                  <th className="px-4 py-3 font-semibold text-right">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {(data ?? []).map((u) => {
                  const editando = editId === u.id;
                  return (
                    <tr key={u.id} className="border-b border-linea last:border-0 align-top">
                      <td className="px-4 py-3 font-medium text-carbon">{u.nombre}</td>
                      <td className="px-4 py-3 text-carbon-suave">{u.email}</td>
                      <td className="px-4 py-3">
                        {editando ? (
                          <Select value={eNivel} onChange={(e) => setENivel(Number(e.target.value))} className="w-44">
                            {[1, 2, 3, 4].map((n) => (
                              <option key={n} value={n}>{NIVEL_LABEL[n]}</option>
                            ))}
                          </Select>
                        ) : (
                          <span className="flex items-center gap-2 text-carbon-suave">
                            {u.nivel_jerarquico}
                            {u.nivel_jerarquico <= NIVEL_MAX_FIRMANTE && (
                              <Chip className="border-firmado/40 bg-firmado/10 text-firmado">Firmante</Chip>
                            )}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {editando ? (
                          <Select value={eRol} onChange={(e) => setERol(e.target.value)} className="w-48">
                            {ROLES.map((r) => (
                              <option key={r} value={r}>{ROL_LABEL[r] ?? r}</option>
                            ))}
                          </Select>
                        ) : (
                          <div className="flex flex-wrap gap-1">
                            {u.roles.length === 0 ? (
                              <span className="text-carbon-suave">—</span>
                            ) : (
                              u.roles.map((r, i) => <Chip key={i}>{ROL_LABEL[r.rol] ?? r.rol}</Chip>)
                            )}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {editando ? (
                          <Select
                            value={ePropiedad}
                            onChange={(e) => setEPropiedad(e.target.value)}
                            className="w-40"
                          >
                            <option value="">Corporativo (todas)</option>
                            {(propiedades ?? []).map((p) => (
                              <option key={p.id} value={p.id}>{p.codigo}</option>
                            ))}
                          </Select>
                        ) : u.roles[0]?.propiedad_id ? (
                          <Chip>{propNombre.get(u.roles[0].propiedad_id) ?? "propiedad"}</Chip>
                        ) : (
                          <span className="text-carbon-suave">Corporativo</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {editando ? (
                          <label className="flex items-center gap-1 text-xs text-carbon-suave">
                            <input type="checkbox" checked={eActivo} onChange={(e) => setEActivo(e.target.checked)} />
                            activo
                          </label>
                        ) : u.activo ? (
                          <span className="text-carbon-suave">Activo</span>
                        ) : (
                          <Chip className="border-archivado/40 text-archivado">Inactivo</Chip>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        {editando ? (
                          <div className="flex justify-end gap-2">
                            <Button onClick={() => guardarEdicion(u.id)} disabled={actualizar.isPending}>
                              Guardar
                            </Button>
                            <Button variant="secondary" onClick={() => setEditId(null)}>
                              Cancelar
                            </Button>
                          </div>
                        ) : (
                          <button
                            onClick={() => abrirEdicion(u)}
                            className="text-xs text-petrol-oscuro hover:underline"
                          >
                            Editar
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
