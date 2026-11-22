import { Icon } from '../components/Icon';

/** HU-01.2 / LFPDPPP: aviso de privacidad integral, enlazado desde el registro. */
export function PrivacyNoticePage() {
  return (
    <main className="report-page">
      <section className="report-intro" aria-labelledby="aviso-titulo">
        <h1 id="aviso-titulo">Aviso de privacidad</h1>
        <p>Calles Seguras Juárez, Asociación Civil, con domicilio en Ciudad Juárez, Chihuahua, es responsable del tratamiento de tus datos personales conforme a la Ley Federal de Protección de Datos Personales en Posesión de los Particulares (LFPDPPP).</p>
      </section>

      <section className="report-section" aria-labelledby="aviso-datos">
        <h2 id="aviso-datos">¿Qué datos recabamos?</h2>
        <ul>
          <li>Nombre y correo electrónico, para crear y proteger tu cuenta.</li>
          <li>Tu contraseña, que guardamos cifrada de forma irreversible: nadie puede leerla.</li>
          <li>La ubicación, la calle, la colonia y la descripción de los daños que reportas.</li>
        </ul>
        <p>No recabamos datos personales sensibles.</p>
      </section>

      <section className="report-section" aria-labelledby="aviso-finalidades">
        <h2 id="aviso-finalidades">¿Para qué los usamos?</h2>
        <ul>
          <li>Registrar tus reportes de baches, alcantarillas sin tapa y encharcamientos, y darles seguimiento.</li>
          <li>Evitar abusos: limitar a 10 reportes por hora por cuenta y validar que los reportes sean reales.</li>
          <li>Generar estadísticas anónimas sobre el estado de las calles de Ciudad Juárez.</li>
        </ul>
      </section>

      <section className="report-section" aria-labelledby="aviso-publico">
        <h2 id="aviso-publico"><Icon name="shield" size={20} />¿Qué se publica?</h2>
        <p>Las consultas públicas muestran sólo los datos del daño (tipo, ubicación, calle, colonia, estado y fechas). <strong>Nunca se publica tu nombre, tu correo ni ningún dato que te identifique.</strong> No vendemos ni compartimos tus datos con terceros; sólo los entregaríamos a una autoridad que los requiera conforme a la ley.</p>
        <p>Por trazabilidad, un reporte que ya fue revisado no se elimina; si no procede se marca como «Rechazado» y deja de mostrarse al público.</p>
      </section>

      <section className="report-section" aria-labelledby="aviso-arco">
        <h2 id="aviso-arco">Tus derechos ARCO</h2>
        <p>Puedes solicitar el acceso, la rectificación o la cancelación de tus datos personales, u oponerte a su uso, así como revocar tu consentimiento, mediante una solicitud a la asociación a través de sus medios de contacto institucionales. Te responderemos en los plazos que establece la LFPDPPP.</p>
        <p>Si este aviso cambia, lo publicaremos en esta misma página.</p>
      </section>

      <p><a className="button button--primary" href="/registro"><Icon name="arrowLeft" size={18} />Volver al registro</a></p>
    </main>
  );
}
