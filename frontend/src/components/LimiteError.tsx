import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props {
  /** Lo que se muestra si algún hijo lanza un error al renderizar (p. ej. una falla de Leaflet). */
  respaldo: ReactNode;
  children: ReactNode;
}

/**
 * Límite de error acotado: una falla en un widget (mapa, gráfica) no desmonta la página completa.
 * React solo ofrece límites de error como componentes de clase.
 */
export class LimiteError extends Component<Props, { fallo: boolean }> {
  state = { fallo: false };

  static getDerivedStateFromError() {
    return { fallo: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Falla aislada en un componente de la página:', error, info.componentStack);
  }

  render() {
    return this.state.fallo ? this.props.respaldo : this.props.children;
  }
}
