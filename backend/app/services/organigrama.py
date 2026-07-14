"""Construcción del árbol jerárquico del organigrama a partir de `reporta_a` (§8.14).

Puro (sin dependencias de DB): recibe una lista de nodos planos y devuelve el bosque
de raíces con sus hijos anidados. Es defensivo ante:
- huérfanos (el jefe no existe o fue eliminado) → se tratan como raíz,
- auto-referencias (`reporta_a` == propio id) → raíz,
- ciclos (A→B→A) → se corta el enlace que cierra el ciclo, garantizando un bosque
  acíclico y evitando recursión infinita al serializar.
"""

from typing import Any


def construir_arbol(
    nodos: list[dict[str, Any]],
    id_key: str = "id",
    parent_key: str = "reporta_a_id",
    hijos_key: str = "hijos",
) -> list[dict[str, Any]]:
    por_id = {n[id_key]: n for n in nodos}

    # Padre efectivo: solo si existe en el conjunto y no es uno mismo.
    padre: dict[Any, Any] = {}
    for nid, n in por_id.items():
        pid = n.get(parent_key)
        padre[nid] = pid if (pid in por_id and pid != nid) else None

    # Cortar ciclos: al subir por la cadena, si se revisita un nodo, se corta ahí.
    for nid in list(padre):
        visto: set[Any] = set()
        cur = nid
        while cur is not None:
            if cur in visto:
                padre[cur] = None  # rompe el ciclo tratándolo como raíz
                break
            visto.add(cur)
            cur = padre[cur]

    salida = {nid: {**por_id[nid], hijos_key: []} for nid in por_id}
    raices: list[dict[str, Any]] = []
    for nid, nodo in salida.items():
        pid = padre[nid]
        if pid is None:
            raices.append(nodo)
        else:
            salida[pid][hijos_key].append(nodo)

    def ordenar(lst: list[dict[str, Any]]) -> None:
        lst.sort(key=lambda x: (x.get("nivel_jerarquico", 99), x.get("codigo", "")))
        for x in lst:
            ordenar(x[hijos_key])

    ordenar(raices)
    return raices
